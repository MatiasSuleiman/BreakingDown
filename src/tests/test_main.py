from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import Controlador_de_aplicacion


class FakeSignal:
    def __init__(self):
        self.connected = []

    def connect(self, callback):
        self.connected.append(callback)


class FakeWindow:
    def __init__(self):
        self.show_calls = 0
        self.close_calls = 0

    def show(self):
        self.show_calls += 1

    def close(self):
        self.close_calls += 1


class FakeLogin:
    def __init__(self):
        self.ventana = FakeWindow()
        self.senal_de_login_exitoso = FakeSignal()


class FakeGui:
    def __init__(self, sistema, al_volver_al_login=None):
        self.sistema = sistema
        self.al_volver_al_login = al_volver_al_login
        self.ventana = FakeWindow()


def test_controlador_muestra_el_login_al_iniciar(monkeypatch):
    monkeypatch.setattr("main.Ventana_de_login", FakeLogin)

    controlador = Controlador_de_aplicacion()

    assert isinstance(controlador.interfaz_principal, FakeLogin)
    assert controlador.interfaz_principal.ventana.show_calls == 1
    assert controlador.interfaz_principal.senal_de_login_exitoso.connected == [
        controlador.al_iniciar_sesion_exitoso
    ]


def test_controlador_puede_volver_del_gui_al_login(monkeypatch):
    monkeypatch.setattr("main.Ventana_de_login", FakeLogin)
    monkeypatch.setattr("main.Gui", FakeGui)

    controlador = Controlador_de_aplicacion()
    login_inicial = controlador.interfaz_principal

    controlador.al_iniciar_sesion_exitoso("sistema")
    gui = controlador.interfaz_principal

    assert isinstance(gui, FakeGui)
    assert gui.al_volver_al_login == controlador.volver_al_login
    assert login_inicial.ventana.close_calls == 1

    controlador.volver_al_login()

    assert isinstance(controlador.interfaz_principal, FakeLogin)
    assert controlador.interfaz_principal is not login_inicial
    assert controlador.interfaz_principal.ventana.show_calls == 1
    assert gui.ventana.close_calls == 1
