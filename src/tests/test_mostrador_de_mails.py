import os
from datetime import datetime
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mostrador_de_mails import Mostrador_de_mails_buscados, Mostrador_de_mails_del_break


class FakeUi:
    def __init__(self):
        self.minutos_por_mail = {}

    def ver_mail(self, _mail):
        pass

    def agregar_mail(self, _mail):
        pass

    def quitar_mail(self, _mail):
        pass

    def cambiar_descripcion_de(self, _mail, _descripcion):
        pass

    def ver_descripcion_de(self, _mail):
        return ""

    def cambiar_minutos_de(self, mail, minutos):
        self.minutos_por_mail[mail] = minutos

    def ver_minutos_de(self, mail):
        return self.minutos_por_mail.get(mail, 0)


class FakeMail:
    def __init__(self, uid="mail-1"):
        self.uid = uid
        self.subject = "Invoice"
        self.from_ = "lawyer@example.com"
        self.date = datetime(2026, 3, 6, 12, 0, 0)
        self.text = "body"


def make_mail(uid="mail-1"):
    return FakeMail(uid)


def get_app():
    return QApplication.instance() or QApplication([])


def test_mostrador_del_break_muestra_barra_de_minutos():
    app = get_app()
    master = QWidget()
    ui = FakeUi()
    mail = make_mail()
    mostrador = Mostrador_de_mails_del_break.en(master, 700, 610, 20, 180, ui)

    mostrador.mostrar([mail])

    barras = mostrador.contenedor_de_mails.findChildren(QLineEdit)
    etiquetas = [label.text() for label in mostrador.contenedor_de_mails.findChildren(QLabel)]

    assert len(barras) == 1
    assert barras[0].text() == "0"
    assert barras[0].maxLength() == 4
    assert isinstance(barras[0].validator(), QIntValidator)
    assert "Minutes:" in etiquetas
    app.quit()


def test_mostrador_de_encontrados_no_muestra_barra_de_minutos():
    app = get_app()
    master = QWidget()
    ui = FakeUi()
    mail = make_mail()
    mostrador = Mostrador_de_mails_buscados.en(master, 700, 610, 20, 180, ui)

    mostrador.mostrar([mail])

    assert mostrador.contenedor_de_mails.findChildren(QLineEdit) == []
    app.quit()


def test_barra_de_minutos_actualiza_el_valor_del_mail():
    app = get_app()
    master = QWidget()
    ui = FakeUi()
    mail = make_mail()
    mostrador = Mostrador_de_mails_del_break.en(master, 700, 610, 20, 180, ui)

    mostrador.mostrar([mail])
    barra = mostrador.contenedor_de_mails.findChildren(QLineEdit)[0]
    barra.setText("1234")

    assert ui.ver_minutos_de(mail) == 1234
    assert barra.maxLength() == 4
    app.quit()


def test_mostrador_puede_actualizar_un_mail_a_match_por_asunto():
    app = get_app()
    master = QWidget()
    ui = FakeUi()
    mail = make_mail()
    mostrador = Mostrador_de_mails_buscados.en(master, 700, 610, 20, 180, ui)

    mostrador.agregar_mail_por_cuerpo(mail)
    mostrador.actualizar_mail_a_asunto(mail)

    tarjetas = mostrador.contenedor_de_mails.findChildren(QWidget, "mailCard")

    assert len(tarjetas) == 1
    assert tarjetas[0].property("matchRole") == "subject"
    app.quit()


def test_mostrador_registra_lotes_en_un_solo_render():
    app = get_app()
    master = QWidget()
    ui = FakeUi()
    mail_de_cuerpo = make_mail("mail-1")
    mail_de_asunto = make_mail("mail-1")
    mostrador = Mostrador_de_mails_buscados.en(master, 700, 610, 20, 180, ui)
    renders = []
    render_original = mostrador._renderizar_desde_estado

    def render_con_conteo(*args, **kwargs):
        renders.append((args, kwargs))
        return render_original(*args, **kwargs)

    mostrador._renderizar_desde_estado = render_con_conteo

    mostrador.registrar_lotes_de_busqueda(
        mails_por_cuerpo=[mail_de_cuerpo],
        mails_actualizados_a_asunto=[mail_de_asunto],
    )

    tarjetas = mostrador.contenedor_de_mails.findChildren(QWidget, "mailCard")

    assert len(renders) == 1
    assert len(tarjetas) == 1
    assert tarjetas[0].property("matchRole") == "subject"
    app.quit()
