from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from errores import GoogleOAuthError
from ventana_de_login import Ventana_de_login


def test_obtener_sesion_google_recupera_una_sesion_guardada_fallida_con_otra_cuenta(monkeypatch):
    ventana = SimpleNamespace()
    llamadas = []

    def falla_cargar_sesion_guardada():
        raise GoogleOAuthError("No se pudo obtener el correo del usuario autenticado en Google.")

    def fake_iniciar_sesion_google(forzar_nueva=False, seleccionar_cuenta=False):
        llamadas.append((forzar_nueva, seleccionar_cuenta))
        return "sesion-google"

    monkeypatch.setattr("ventana_de_login.cargar_sesion_google_guardada", falla_cargar_sesion_guardada)
    monkeypatch.setattr("ventana_de_login.iniciar_sesion_google", fake_iniciar_sesion_google)
    ventana.preguntar_como_recuperar_oauth_de_google = lambda error, contexto=None: "otra"
    ventana.preguntar_como_continuar_con_google = lambda user: "continuar"
    ventana.ejecutar_oauth_de_google = lambda forzar_nueva=False, seleccionar_cuenta=False: (
        Ventana_de_login.ejecutar_oauth_de_google(
            ventana,
            forzar_nueva=forzar_nueva,
            seleccionar_cuenta=seleccionar_cuenta,
        )
    )
    ventana.recuperar_oauth_de_google = lambda contexto, error: Ventana_de_login.recuperar_oauth_de_google(
        ventana,
        contexto,
        error,
    )

    assert Ventana_de_login.obtener_sesion_google(ventana) == "sesion-google"
    assert llamadas == [(True, True)]


def test_ejecutar_oauth_de_google_reintenta_con_un_nuevo_flujo(monkeypatch):
    ventana = SimpleNamespace()
    llamadas = []

    def fake_iniciar_sesion_google(forzar_nueva=False, seleccionar_cuenta=False):
        llamadas.append((forzar_nueva, seleccionar_cuenta))
        if len(llamadas) == 1:
            raise GoogleOAuthError("No se pudo obtener el correo del usuario autenticado en Google.")
        return "sesion-google"

    respuestas = iter(["reintentar"])

    monkeypatch.setattr("ventana_de_login.iniciar_sesion_google", fake_iniciar_sesion_google)
    ventana.preguntar_como_recuperar_oauth_de_google = lambda error, contexto=None: next(respuestas)

    assert Ventana_de_login.ejecutar_oauth_de_google(ventana) == "sesion-google"
    assert llamadas == [(False, False), (False, False)]


def test_obtener_sistema_con_google_reintenta_el_login_imap_con_la_misma_sesion(monkeypatch):
    sesion_google = SimpleNamespace(user="lawyer@example.com")
    buscador = object()
    sistema = object()
    ventana = SimpleNamespace()
    llamadas = []

    def fake_login_con_oauth2(sesion):
        llamadas.append(sesion)
        if len(llamadas) == 1:
            raise GoogleOAuthError("imap offline")
        return buscador

    monkeypatch.setattr("ventana_de_login.Buscador_adapter.login_con_oauth2", fake_login_con_oauth2)
    monkeypatch.setattr("ventana_de_login.System_Facade.build", lambda user, buscador_recibido: sistema)

    ventana.obtener_sesion_google = lambda: sesion_google
    respuestas = iter(["reintentar"])
    ventana.preguntar_como_recuperar_oauth_de_google = lambda error, contexto=None: next(respuestas)
    ventana.ejecutar_oauth_de_google = lambda forzar_nueva=False, seleccionar_cuenta=False: None

    assert Ventana_de_login.obtener_sistema_con_google(ventana) == (sesion_google, sistema)
    assert llamadas == [sesion_google, sesion_google]


def test_obtener_sistema_con_google_permite_cambiar_de_cuenta_si_falla_el_login_imap(monkeypatch):
    sesion_inicial = SimpleNamespace(user="old@example.com")
    sesion_nueva = SimpleNamespace(user="new@example.com")
    buscador = object()
    sistema = object()
    ventana = SimpleNamespace()
    llamadas = []

    def fake_login_con_oauth2(sesion):
        llamadas.append(sesion)
        if sesion is sesion_inicial:
            raise GoogleOAuthError("imap rejected")
        return buscador

    monkeypatch.setattr("ventana_de_login.Buscador_adapter.login_con_oauth2", fake_login_con_oauth2)
    monkeypatch.setattr("ventana_de_login.System_Facade.build", lambda user, buscador_recibido: sistema)

    ventana.obtener_sesion_google = lambda: sesion_inicial
    respuestas = iter(["otra"])
    ventana.preguntar_como_recuperar_oauth_de_google = lambda error, contexto=None: next(respuestas)
    ventana.ejecutar_oauth_de_google = (
        lambda forzar_nueva=False, seleccionar_cuenta=False: sesion_nueva
        if (forzar_nueva, seleccionar_cuenta) == (True, True)
        else None
    )

    assert Ventana_de_login.obtener_sistema_con_google(ventana) == (sesion_nueva, sistema)
    assert llamadas == [sesion_inicial, sesion_nueva]
