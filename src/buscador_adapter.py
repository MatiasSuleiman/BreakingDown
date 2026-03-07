import socket
import time
import imaplib
from functools import reduce

from imap_tools import MailBox, AND
from imap_tools.errors import UnexpectedCommandStatusError

try:
    from src.errores import CredencialesInvalidasError
except ModuleNotFoundError:
    from errores import CredencialesInvalidasError


def cumple_todo(mail, condiciones):
    return reduce(lambda x, y: x and y.cumple(mail), condiciones, True)


def concatenacion_de_todos_los_elementos_de(data):
    partes = []
    for item in data:
        if isinstance(item, (bytes, bytearray)):
            partes.append(bytes(item))
        else:
            partes.append(str(item).encode("utf-8", errors="ignore"))
    return b" ".join(partes).decode("utf-8", errors="ignore")


def es_error_de_autenticacion(error):
    if hasattr(error, "command_result"):
        try:
            command_result = error.command_result
            data = command_result[1]
            if isinstance(data, (list, tuple)):
                detalle = concatenacion_de_todos_los_elementos_de(data).upper()
                return "AUTHENTICATIONFAILED" in detalle
        except Exception:
            pass
    return "AUTHENTICATIONFAILED" in str(error).upper()


ERRORES_TRANSITORIOS_DE_RED = (socket.gaierror, socket.timeout, TimeoutError)
IMAP_TIMEOUT_S = 15

class Buscador_adapter:
    ALIAS_DE_CARPETAS = {
        "INBOX": ("INBOX",),
        "[Gmail]/Sent Mail": ("[Gmail]/Sent Mail", "[Gmail]/Enviados"),
        "[Gmail]/Enviados": ("[Gmail]/Enviados", "[Gmail]/Sent Mail"),
    }

    def __init__(self, mailbox, user, password=None, sesion_google=None):
        self.mailbox = mailbox
        self.user = user
        self.password = password
        self.sesion_google = sesion_google
        self.carpeta_actual = "INBOX"

    @classmethod
    def login(cls, user, password, retries=3, delay_s=1, folder="INBOX"):
        last_error = None
        for _ in range(retries):
            try:
                mailbox = MailBox("imap.gmail.com", timeout=IMAP_TIMEOUT_S).login(user, password, folder)
                return cls(mailbox, user, password)
            except (UnexpectedCommandStatusError, imaplib.IMAP4.error) as error:
                if es_error_de_autenticacion(error):
                    raise CredencialesInvalidasError() from error
                raise
            except ERRORES_TRANSITORIOS_DE_RED as error:
                last_error = error
                time.sleep(delay_s)
        raise last_error

    @classmethod
    def login_con_oauth2(cls, sesion_google, retries=3, delay_s=1, folder="INBOX"):
        last_error = None
        for _ in range(retries):
            try:
                mailbox = MailBox("imap.gmail.com", timeout=IMAP_TIMEOUT_S).xoauth2(
                    sesion_google.user,
                    sesion_google.access_token(),
                    folder,
                )
                return cls(
                    mailbox,
                    sesion_google.user,
                    sesion_google=sesion_google,
                )
            except (UnexpectedCommandStatusError, imaplib.IMAP4.error) as error:
                if es_error_de_autenticacion(error):
                    sesion_google.refrescar()
                    last_error = error
                    continue
                raise
            except ERRORES_TRANSITORIOS_DE_RED as error:
                last_error = error
                time.sleep(delay_s)
        raise last_error

    def relogin_en(self, folder):
        if self.sesion_google is not None:
            nuevo_buscador = self.__class__.login_con_oauth2(
                self.sesion_google,
                folder=folder,
            )
        else:
            nuevo_buscador = self.__class__.login(self.user, self.password, folder=folder)
        self.mailbox = nuevo_buscador.mailbox

    def cambiar_carpeta(self, carpeta):
        self.carpeta_actual = carpeta
        self.seleccionar_carpeta_actual()

    def carpetas_posibles(self):
        return self.ALIAS_DE_CARPETAS.get(self.carpeta_actual, (self.carpeta_actual,))

    def seleccionar_carpeta_actual(self):
        ultimo_error = None

        for carpeta in self.carpetas_posibles():
            try:
                self.mailbox.folder.set(carpeta, readonly=True)
                self.carpeta_actual = carpeta
                return
            except UnexpectedCommandStatusError as error:
                ultimo_error = error

        for carpeta in self.carpetas_posibles():
            try:
                self.relogin_en(carpeta)
                self.carpeta_actual = carpeta
                return
            except UnexpectedCommandStatusError as error:
                ultimo_error = error

        raise ultimo_error

    def encontrar_de_a_partes(self, asunto, condiciones):
        asunto = asunto.strip()
        criterio = AND(subject=asunto)
        for mail in self.mailbox.fetch(criterio, bulk=10, reverse=True):
            if cumple_todo(mail, condiciones):
                yield mail
