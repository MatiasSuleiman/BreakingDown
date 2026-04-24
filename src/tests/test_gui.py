import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QSizePolicy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui import Gui


class FakeBuscador:
    def __init__(self):
        self.carpeta_actual = "INBOX"

    def cambiar_carpeta(self, carpeta):
        self.carpeta_actual = carpeta


class FakeSistema:
    def __init__(self):
        self.buscador = FakeBuscador()
        self.mails_del_breakdown = []
        self.mails_encontrados = []

    def ver_todos_los_mails_encontrados(self):
        return list(self.mails_encontrados)

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

    def cantidad_de_encontrados(self):
        return len(self.mails_encontrados)


def get_app():
    return QApplication.instance() or QApplication([])


def test_gui_inicia_con_filtros_ocultos():
    app = get_app()
    gui = Gui(FakeSistema())
    app.processEvents()

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
    app.processEvents()
    ancho_inicial = gui.panel_de_controles.width()

    gui.boton_de_filtros.click()
    app.processEvents()

    assert gui.cuerpo_de_filtros.isHidden() is False
    assert gui.boton_de_filtros.text() == Gui.TEXTO_BOTON_FILTROS_EXPANDIDO
    assert abs(gui.panel_de_controles.width() - ancho_inicial) <= 2

    gui.boton_de_filtros.click()
    app.processEvents()

    assert gui.cuerpo_de_filtros.isHidden() is True
    assert gui.boton_de_filtros.text() == Gui.TEXTO_BOTON_FILTROS_COLAPSADO
    assert abs(gui.panel_de_controles.width() - ancho_inicial) <= 2

    gui.ventana.close()
    app.quit()


def test_filtros_conservan_valores_al_ocultarse_y_mostrarse():
    app = get_app()
    gui = Gui(FakeSistema())

    gui.boton_de_filtros.click()
    app.processEvents()

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
