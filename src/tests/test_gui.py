import os
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QSizePolicy, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui import Gui


class FakeBuscador:
    def __init__(self):
        self.carpeta_actual = "INBOX"

    def cambiar_carpeta(self, carpeta):
        self.carpeta_actual = carpeta


class FakeSistema:
    def __init__(self, resultados_por_asunto=None, resultados_por_cuerpo=None):
        self.buscador_por_asunto = FakeBuscador()
        self.buscador_por_cuerpo = FakeBuscador()
        self.buscador = self.buscador_por_asunto
        self.mails_del_breakdown = []
        self.mails_encontrados = []
        self.resultados_por_asunto = list(resultados_por_asunto or [])
        self.resultados_por_cuerpo = list(resultados_por_cuerpo or [])
        self.llamadas_por_asunto = []
        self.llamadas_por_cuerpo = []

    def ver_todos_los_mails_encontrados(self):
        return list(self.mails_encontrados)

    def cambiar_carpeta_de_busqueda(self, carpeta):
        self.buscador_por_asunto.cambiar_carpeta(carpeta)
        self.buscador_por_cuerpo.cambiar_carpeta(carpeta)

    def buscar_de_a_partes_por_asunto(self, texto):
        self.llamadas_por_asunto.append(texto)
        return iter(self.resultados_por_asunto)

    def buscar_de_a_partes_por_cuerpo(self, texto):
        self.llamadas_por_cuerpo.append(texto)
        return iter(self.resultados_por_cuerpo)

    def limpiar_condiciones(self):
        pass

    def agregar_condicion_de_emisor(self, _valor):
        pass

    def agregar_condicion_de_receptor(self, _valor):
        pass

    def agregar_condicion_de_enviado_antes_de(self, _valor):
        pass

    def agregar_condicion_de_enviado_despues_de(self, _valor):
        pass

    def agregar_condicion_de_cuerpo(self, _valor):
        pass

    def limpiar_encontrados(self):
        self.mails_encontrados = []

    def agregar_mails_encontrados(self, mails):
        self.mails_encontrados.extend(mails)

    def agregar_mail_encontrado(self, mail):
        self.mails_del_breakdown.append(mail)
        self.mails_encontrados.remove(mail)

    def quitar_mail_del_breakdown(self, mail):
        self.mails_del_breakdown.remove(mail)
        self.mails_encontrados.append(mail)

    def cambiar_descripcion_de(self, _mail, _descripcion):
        pass

    def ver_descripcion_de(self, _mail):
        return ""

    def cambiar_minutos_de(self, _mail, _minutos):
        pass

    def ver_minutos_de(self, _mail):
        return 0

    def cantidad_de_encontrados(self):
        return len(self.mails_encontrados)


def make_mail(uid, subject="Invoice", body="invoice body", date=None):
    return SimpleNamespace(
        uid=uid,
        subject=subject,
        from_="lawyer@example.com",
        date=date or datetime(2026, 3, 6, 12, 0, 0),
        text=body,
    )


def get_app():
    return QApplication.instance() or QApplication([])


def wait_for_searches_to_finish(app, gui, max_cycles=50):
    for _ in range(max_cycles):
        app.processEvents()
        if not gui.busqueda_en_curso:
            break


def flush_qt_events(app, cycles=3):
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


def test_gui_inicia_con_filtros_ocultos():
    app = get_app()
    gui = Gui(FakeSistema())
    flush_qt_events(app)

    assert gui.cuerpo_de_filtros.isHidden() is True
    assert gui.boton_de_filtros.text() == Gui.TEXTO_BOTON_FILTROS_COLAPSADO
    assert gui.boton_de_filtros.parent() is gui.slot_de_filtros
    assert gui.boton_de_filtros.x() < gui.panel_de_controles.x()
    assert gui.slot_de_filtros.y() == gui.panel_de_controles.y()
    assert gui.mostrador_de_condiciones.caja_filtros.title() == ""
    assert gui.boton_de_filtros.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Fixed

    gui.ventana.close()
    app.quit()


def test_toggle_de_filtros_muestra_y_oculta_el_panel_sin_mover_el_panel_derecho():
    app = get_app()
    gui = Gui(FakeSistema())
    flush_qt_events(app)
    ancho_inicial = gui.panel_de_controles.width()

    gui.boton_de_filtros.click()
    flush_qt_events(app)

    assert gui.cuerpo_de_filtros.isHidden() is False
    assert gui.boton_de_filtros.text() == Gui.TEXTO_BOTON_FILTROS_EXPANDIDO
    assert abs(gui.panel_de_controles.width() - ancho_inicial) <= 2

    gui.boton_de_filtros.click()
    flush_qt_events(app)

    assert gui.cuerpo_de_filtros.isHidden() is True
    assert gui.boton_de_filtros.text() == Gui.TEXTO_BOTON_FILTROS_COLAPSADO
    assert abs(gui.panel_de_controles.width() - ancho_inicial) <= 2

    gui.ventana.close()
    app.quit()


def test_filtros_conservan_valores_al_ocultarse_y_mostrarse():
    app = get_app()
    gui = Gui(FakeSistema())

    gui.boton_de_filtros.click()
    flush_qt_events(app)

    gui.mostrador_de_condiciones.barra_de_emisor.setText("lawyer@example.com")
    gui.mostrador_de_condiciones.barra_de_receptor.setText("client@example.com")
    gui.mostrador_de_condiciones.barra_de_cuerpo.setText("invoice")
    gui.mostrador_de_condiciones.barra_de_enviado_antes_de.setText("24/04/2026")
    gui.mostrador_de_condiciones.barra_de_enviado_despues_de.setText("01/04/2026")

    gui.boton_de_filtros.click()
    gui.boton_de_filtros.click()
    app.processEvents()

    assert gui.mostrador_de_condiciones.barra_de_emisor.text() == "lawyer@example.com"
    assert gui.mostrador_de_condiciones.barra_de_receptor.text() == "client@example.com"
    assert gui.mostrador_de_condiciones.barra_de_cuerpo.text() == "invoice"
    assert gui.mostrador_de_condiciones.barra_de_enviado_antes_de.text() == "24/04/2026"
    assert gui.mostrador_de_condiciones.barra_de_enviado_despues_de.text() == "01/04/2026"

    gui.ventana.close()
    app.quit()


def test_busqueda_vacia_no_dispara_busquedas_en_paralelo():
    app = get_app()
    sistema = FakeSistema()
    gui = Gui(sistema)

    gui.barra_de_busqueda.setText("")
    gui.buscar()
    app.processEvents()

    assert sistema.llamadas_por_asunto == []
    assert sistema.llamadas_por_cuerpo == []
    assert gui.busqueda_en_curso is False
    assert gui.boton_de_busqueda.text() == "Buscar"

    gui.ventana.close()
    app.quit()


def test_busqueda_no_vacia_dispara_ambas_busquedas():
    app = get_app()
    sistema = FakeSistema(
        resultados_por_asunto=[make_mail("1", subject="Invoice")],
        resultados_por_cuerpo=[make_mail("2", subject="Body hit")],
    )
    gui = Gui(sistema)

    gui.barra_de_busqueda.setText("invoice")
    gui.buscar()
    wait_for_searches_to_finish(app, gui)
    app.processEvents()

    assert sistema.llamadas_por_asunto == ["invoice"]
    assert sistema.llamadas_por_cuerpo == ["invoice"]
    assert gui.busqueda_en_curso is False
    assert gui.sistema.cantidad_de_encontrados() == 2

    gui.ventana.close()
    app.quit()


def test_mail_de_cuerpo_que_luego_llega_por_asunto_se_actualiza_sin_duplicarse_y_conserva_color():
    app = get_app()
    gui = Gui(FakeSistema())
    mail_por_cuerpo = make_mail("42", subject="Invoice", body="invoice body")
    mail_por_asunto = make_mail("42", subject="Invoice", body="different instance")

    gui.al_recibir_lote_de_cuerpo([mail_por_cuerpo])
    gui.al_recibir_lote_de_asunto([mail_por_asunto])
    app.processEvents()

    tarjetas_encontradas = gui.mostrador_de_mails_encontrados.contenedor_de_mails.findChildren(
        QWidget, "mailCard"
    )

    assert len(tarjetas_encontradas) == 1
    assert tarjetas_encontradas[0].property("matchRole") == "subject"
    assert gui.sistema.cantidad_de_encontrados() == 1

    gui.agregar_mail(mail_por_cuerpo)
    gui.quitar_mail(mail_por_cuerpo)
    app.processEvents()

    tarjetas_encontradas = gui.mostrador_de_mails_encontrados.contenedor_de_mails.findChildren(
        QWidget, "mailCard"
    )
    tarjetas_break = gui.mostrador_de_mails_del_break.contenedor_de_mails.findChildren(
        QWidget, "mailCard"
    )

    assert len(tarjetas_break) == 0
    assert len(tarjetas_encontradas) == 1
    assert tarjetas_encontradas[0].property("matchRole") == "subject"

    gui.ventana.close()
    app.quit()


def test_gui_preserva_scroll_al_recibir_un_lote_de_resultados():
    app = get_app()
    gui = Gui(FakeSistema())
    fecha_base = datetime(2026, 3, 6, 12, 0, 0)

    gui.al_recibir_lote_de_asunto(
        [
            make_mail(
                str(indice),
                date=fecha_base + timedelta(minutes=indice),
            )
            for indice in range(30)
        ]
    )
    flush_qt_events(app)

    scroll = gui.mostrador_de_mails_encontrados.area.verticalScrollBar()
    assert scroll.maximum() > 0
    valor_esperado = max(1, scroll.maximum() // 2)
    scroll.setValue(valor_esperado)
    flush_qt_events(app)
    clave_visible, desplazamiento_visible = primer_mail_visible(gui.mostrador_de_mails_encontrados)

    gui.al_recibir_lote_de_asunto(
        [
            make_mail(
                f"nuevo-{indice}",
                date=fecha_base + timedelta(minutes=60 + indice),
            )
            for indice in range(3)
        ]
    )
    flush_qt_events(app)

    nueva_clave_visible, nuevo_desplazamiento_visible = primer_mail_visible(
        gui.mostrador_de_mails_encontrados
    )
    assert nueva_clave_visible == clave_visible
    assert abs(nuevo_desplazamiento_visible - desplazamiento_visible) <= 1
    gui.ventana.close()
    app.quit()


def test_gui_coalescea_lotes_pendientes_en_un_solo_render():
    app = get_app()
    gui = Gui(FakeSistema())
    llamadas_de_render = []
    registrar_original = gui.mostrador_de_mails_encontrados.registrar_lotes_de_busqueda

    def registrar_con_conteo(*args, **kwargs):
        llamadas_de_render.append(kwargs)
        return registrar_original(*args, **kwargs)

    gui.mostrador_de_mails_encontrados.registrar_lotes_de_busqueda = registrar_con_conteo

    gui.al_recibir_lote_de_cuerpo([make_mail("1", subject="Body hit")])
    gui.al_recibir_lote_de_asunto([make_mail("2", subject="Subject hit")])
    flush_qt_events(app)

    tarjetas_encontradas = gui.mostrador_de_mails_encontrados.contenedor_de_mails.findChildren(
        QWidget, "mailCard"
    )

    assert len(llamadas_de_render) == 1
    assert len(tarjetas_encontradas) == 2
    assert gui.sistema.cantidad_de_encontrados() == 2

    gui.ventana.close()
    app.quit()


def test_gui_clampea_scroll_si_el_contenido_deja_de_tener_scroll():
    app = get_app()
    gui = Gui(FakeSistema())

    gui.mostrador_de_mails_encontrados.restaurar_scroll_vertical(9999)

    scroll = gui.mostrador_de_mails_encontrados.area.verticalScrollBar()
    assert scroll.value() == 0

    gui.ventana.close()
    app.quit()


def test_gui_no_finaliza_busqueda_hasta_renderizar_lotes_pendientes():
    app = get_app()
    gui = Gui(FakeSistema())
    gui.busqueda_en_curso = True
    gui.busquedas_activas = {"asunto"}

    gui.al_recibir_lote_de_asunto([make_mail("1")])
    gui.al_finalizar_busqueda_de("asunto")

    assert gui.busqueda_en_curso is True

    flush_qt_events(app)

    assert gui.busqueda_en_curso is False
    assert gui.boton_de_busqueda.text() == "Buscar"
    assert gui.sistema.cantidad_de_encontrados() == 1

    gui.ventana.close()
    app.quit()
