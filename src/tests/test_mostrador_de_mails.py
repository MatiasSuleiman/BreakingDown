import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QVBoxLayout, QWidget

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
    def __init__(self, uid="mail-1", date=None):
        self.uid = uid
        self.subject = "Invoice"
        self.from_ = "lawyer@example.com"
        self.date = date or datetime(2026, 3, 6, 12, 0, 0)
        self.text = "body"


def make_mail(uid="mail-1", date=None):
    return FakeMail(uid, date)


def get_app():
    return QApplication.instance() or QApplication([])


def flush_qt_events(app, cycles=6):
    for _ in range(cycles):
        app.processEvents()


def primer_mail_visible(mostrador):
    scroll = mostrador.area.verticalScrollBar()
    valor = scroll.value()
    limite_inferior = valor + mostrador.area.viewport().height()

    for indice in range(mostrador.layout.count()):
        widget = mostrador.layout.itemAt(indice).widget()
        if widget is None:
            continue

        geometria = widget.geometry()
        if geometria.bottom() >= valor and geometria.top() <= limite_inferior:
            return widget.property("mailKey"), geometria.top() - valor

    return None, 0


def crear_mostrador_buscados_con_scroll():
    master = QWidget()
    layout = QVBoxLayout(master)
    layout.setContentsMargins(0, 0, 0, 0)
    ui = FakeUi()
    mostrador = Mostrador_de_mails_buscados.en(master, 700, 610, 20, 180, ui)
    layout.addWidget(mostrador.area)
    master.resize(500, 360)
    master.show()
    return master, mostrador


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


def test_mostrador_preserva_mail_visible_cuando_entran_mails_mas_recientes():
    app = get_app()
    master, mostrador = crear_mostrador_buscados_con_scroll()
    fecha_base = datetime(2026, 3, 6, 12, 0, 0)

    mostrador.mostrar(
        [
            make_mail(
                f"mail-{indice}",
                date=fecha_base + timedelta(minutes=indice),
            )
            for indice in range(40)
        ]
    )
    flush_qt_events(app)

    scroll = mostrador.area.verticalScrollBar()
    assert scroll.maximum() > 0
    scroll.setValue(scroll.maximum() // 2)
    flush_qt_events(app)
    clave_visible, desplazamiento_visible = primer_mail_visible(mostrador)

    mostrador.registrar_lotes_de_busqueda(
        mails_por_asunto=[
            make_mail(
                f"nuevo-{indice}",
                date=fecha_base + timedelta(days=1, minutes=indice),
            )
            for indice in range(5)
        ]
    )
    flush_qt_events(app, cycles=12)

    nueva_clave_visible, nuevo_desplazamiento_visible = primer_mail_visible(mostrador)
    assert nueva_clave_visible == clave_visible
    assert abs(nuevo_desplazamiento_visible - desplazamiento_visible) <= 1
    master.close()
    app.quit()


def test_mostrador_reintenta_restaurar_scroll_si_el_layout_aun_no_tiene_rango():
    app = get_app()
    master, mostrador = crear_mostrador_buscados_con_scroll()
    ancla = {"clave": None, "desplazamiento": 0, "valor": 120}
    generacion = mostrador.generacion_de_scroll

    mostrador.restaurar_scroll_vertical_despues_de_layout(ancla, generacion)
    for indice in range(40):
        mostrador.agregar_mail_renderizado(make_mail(f"mail-{indice}"), False)
    flush_qt_events(app, cycles=12)

    scroll = mostrador.area.verticalScrollBar()
    assert scroll.maximum() >= 120
    assert scroll.value() == 120
    master.close()
    app.quit()


def test_mostrador_ignora_restauracion_de_scroll_vieja():
    app = get_app()
    master, mostrador = crear_mostrador_buscados_con_scroll()
    mostrador.mostrar([make_mail(f"mail-{indice}") for indice in range(40)])
    flush_qt_events(app)

    scroll = mostrador.area.verticalScrollBar()
    scroll.setValue(30)
    generacion_vieja = mostrador.generacion_de_scroll
    mostrador.generacion_de_scroll += 1

    mostrador.restaurar_scroll_vertical_despues_de_layout(
        {"clave": None, "desplazamiento": 0, "valor": 200},
        generacion_vieja,
    )

    assert scroll.value() == 30
    master.close()
    app.quit()
