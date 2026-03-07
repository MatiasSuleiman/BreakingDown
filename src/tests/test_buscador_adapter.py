from pathlib import Path
from types import SimpleNamespace
from datetime import datetime
import sys

from imap_tools.errors import UnexpectedCommandStatusError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from buscador_adapter import Buscador_adapter, IMAP_TIMEOUT_S
from condicion import Condicion_de_cuerpo


class FakeFolder:
    def __init__(self, mailbox, carpetas_invalidas=None):
        self.mailbox = mailbox
        self.carpetas_invalidas = set(carpetas_invalidas or [])

    def set(self, folder, *_args, **_kwargs):
        if folder in self.carpetas_invalidas:
            raise UnexpectedCommandStatusError("bad", (folder,))
        self.mailbox.current_folder = folder
        return None


class FakeMailbox:
    def __init__(self, mails_por_carpeta, carpetas_invalidas=None):
        self.folder = FakeFolder(self, carpetas_invalidas=carpetas_invalidas)
        self._mails_por_carpeta = mails_por_carpeta
        self.current_folder = "INBOX"
        self.last_fetch_criteria = None
        self.fetch_calls = []

    def fetch(self, criteria, bulk=None, reverse=False, headers_only=False, limit=None):
        self.last_fetch_criteria = str(criteria)
        self.fetch_calls.append(
            {
                "criteria": str(criteria),
                "bulk": bulk,
                "reverse": reverse,
                "headers_only": headers_only,
                "limit": limit,
                "folder": self.current_folder,
            }
        )
        mails = list(self._mails_por_carpeta.get(self.current_folder, []))
        criterio_str = str(criteria)
        if criterio_str.startswith('(SUBJECT "') and criterio_str.endswith('")'):
            asunto = criterio_str[len('(SUBJECT "'):-2]
            mails = [mail for mail in mails if asunto.lower() in (mail.subject or "").lower()]
        if reverse:
            mails.reverse()
        if isinstance(limit, int):
            mails = mails[:limit]
        return iter(mails)


def make_mail(uid, subject, body="", message_id=None):
    timestamp = datetime(2026, 3, 6, 12, 0, 0)
    return SimpleNamespace(
        uid=uid,
        subject=subject,
        from_="lawyer@example.com",
        to=("client@example.com",),
        date=timestamp,
        text=body,
        headers={"message-id": (message_id,) if message_id else ()},
    )


class FakeSesionGoogle:
    def __init__(self, user="lawyer@example.com", token="google-token"):
        self.user = user
        self.token = token
        self.access_token_calls = 0
        self.refresh_calls = 0

    def access_token(self):
        self.access_token_calls += 1
        return self.token

    def refrescar_si_es_necesario(self):
        self.refresh_calls += 1


def test_encontrar_de_a_partes_busca_en_la_carpeta_actual():
    mailbox = FakeMailbox(
        {
            "INBOX": [
                make_mail("1", "Other thread"),
                make_mail("2", "Invoice 123"),
            ],
            "[Gmail]/Sent Mail": [
                make_mail("3", "Draft follow-up"),
                make_mail("4", "Re: invoice details"),
            ],
        }
    )
    buscador = Buscador_adapter(mailbox, "user@gmail.com", "secret")
    buscador.cambiar_carpeta("[Gmail]/Sent Mail")

    encontrados = list(
        buscador.encontrar_de_a_partes(
            "invoice",
            [],
        )
    )

    assert [mail.subject for mail in encontrados] == ["Re: invoice details"]
    assert mailbox.last_fetch_criteria == '(SUBJECT "invoice")'
    assert mailbox.fetch_calls == [
        {
            "criteria": '(SUBJECT "invoice")',
            "bulk": 10,
            "reverse": True,
            "headers_only": False,
            "limit": None,
            "folder": "[Gmail]/Sent Mail",
        }
    ]


def test_encontrar_de_a_partes_filtra_por_cuerpo_sin_refetch():
    mailbox = FakeMailbox(
        {
            "INBOX": [make_mail("1", "Invoice 123", body="Please review the invoice")],
            "[Gmail]/Sent Mail": [make_mail("2", "Other thread", body="Nothing relevant here")],
        }
    )
    buscador = Buscador_adapter(mailbox, "user@gmail.com", "secret")

    encontrados = list(
        buscador.encontrar_de_a_partes(
            "",
            [Condicion_de_cuerpo.con_cuerpo("invoice")],
        )
    )

    assert [mail.subject for mail in encontrados] == ["Invoice 123"]
    assert mailbox.fetch_calls == [
        {
            "criteria": '(SUBJECT "")',
            "bulk": 10,
            "reverse": True,
            "headers_only": False,
            "limit": None,
            "folder": "INBOX",
        },
    ]


def test_cambiar_carpeta_hace_que_busque_en_enviados():
    mailbox = FakeMailbox(
        {
            "INBOX": [make_mail("1", "Inbox only")],
            "[Gmail]/Sent Mail": [make_mail("9", "Sent only")],
        }
    )
    buscador = Buscador_adapter(mailbox, "user@gmail.com", "secret")
    buscador.cambiar_carpeta("[Gmail]/Sent Mail")

    encontrados = list(buscador.encontrar_de_a_partes("", []))

    assert [mail.uid for mail in encontrados] == ["9"]


def test_enviados_tiene_fallback_a_carpeta_en_espanol():
    mailbox = FakeMailbox(
        {
            "[Gmail]/Enviados": [make_mail("9", "Sent only")],
        },
        carpetas_invalidas={"[Gmail]/Sent Mail"},
    )
    buscador = Buscador_adapter(mailbox, "user@gmail.com", "secret")
    buscador.cambiar_carpeta("[Gmail]/Sent Mail")

    encontrados = list(buscador.encontrar_de_a_partes("", []))

    assert [mail.uid for mail in encontrados] == ["9"]
    assert mailbox.fetch_calls == [
        {
            "criteria": '(SUBJECT "")',
            "bulk": 10,
            "reverse": True,
            "headers_only": False,
            "limit": None,
            "folder": "[Gmail]/Enviados",
        },
    ]


def test_login_con_oauth2_usa_xoauth2(monkeypatch):
    mailbox = FakeMailbox({"INBOX": []})
    sesion_google = FakeSesionGoogle()

    class FakeMailBoxFactory:
        def __init__(self, _host, timeout=None):
            assert timeout == IMAP_TIMEOUT_S

        def xoauth2(self, user, access_token, folder):
            assert user == "lawyer@example.com"
            assert access_token == "google-token"
            assert folder == "INBOX"
            return mailbox

    monkeypatch.setattr("buscador_adapter.MailBox", FakeMailBoxFactory)

    buscador = Buscador_adapter.login_con_oauth2(sesion_google)

    assert buscador.mailbox is mailbox
    assert buscador.sesion_google is sesion_google
    assert sesion_google.access_token_calls == 1


def test_relogin_en_oauth2_reutiliza_la_sesion_google(monkeypatch):
    mailbox_inicial = FakeMailbox({"INBOX": []})
    mailbox_nuevo = FakeMailbox({"[Gmail]/Sent Mail": []})
    sesion_google = FakeSesionGoogle()
    buscador = Buscador_adapter(
        mailbox_inicial,
        sesion_google.user,
        sesion_google=sesion_google,
    )

    def fake_login_con_oauth2(sesion_recibida, retries=3, delay_s=1, folder="INBOX"):
        assert sesion_recibida is sesion_google
        assert folder == "[Gmail]/Sent Mail"
        return Buscador_adapter(mailbox_nuevo, sesion_google.user, sesion_google=sesion_google)

    monkeypatch.setattr(
        Buscador_adapter,
        "login_con_oauth2",
        classmethod(lambda cls, sesion_recibida, retries=3, delay_s=1, folder="INBOX": fake_login_con_oauth2(sesion_recibida, retries=retries, delay_s=delay_s, folder=folder)),
    )

    buscador.relogin_en("[Gmail]/Sent Mail")

    assert buscador.mailbox is mailbox_nuevo
