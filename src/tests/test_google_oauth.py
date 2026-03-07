from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from errores import GoogleOAuthCredencialesRechazadasError, GoogleOAuthRedError
from google_oauth import (
    CANONICAL_EMAIL_SCOPE,
    LEGACY_EMAIL_SCOPE,
    SCOPES,
    APP_NAME,
    NETWORK_TIMEOUT_S,
    SesionGoogleOAuth,
    borrar_credentials_guardadas,
    cargar_credentials_guardadas,
    cargar_sesion_guardada,
    iniciar_sesion,
    guardar_credentials,
    obtener_user_de,
    ruta_de_client_secret,
    ruta_de_configuracion,
    ruta_de_token,
)


class FakeCredentials:
    def __init__(self, token="token-123", valid=True, refresh_token="refresh-123"):
        self.token = token
        self.valid = valid
        self.refresh_token = refresh_token
        self.refreshed = False

    def to_json(self):
        return json.dumps({"token": self.token})

    def refresh(self, _request):
        self.valid = True
        self.refreshed = True
        self.token = "token-refrescado"


def test_guardar_credentials_persiste_el_json():
    credentials = FakeCredentials()

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        guardar_credentials(credentials, path)

        assert path.read_text(encoding="utf-8") == credentials.to_json()


def test_sesion_google_refresca_y_actualiza_el_archivo(monkeypatch):
    credentials = FakeCredentials(valid=False)
    google_request = object()
    monkeypatch.setattr(
        "google_oauth.imports_de_google",
        lambda: (lambda session=None: google_request, object(), object()),
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        sesion = SesionGoogleOAuth("lawyer@example.com", credentials, path)

        assert sesion.access_token() == "token-refrescado"
        assert credentials.refreshed is True
        assert path.read_text(encoding="utf-8") == credentials.to_json()


def test_obtener_user_de_lee_el_correo_desde_userinfo(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{ "email": "lawyer@example.com" }'

    llamadas = []
    monkeypatch.setattr(
        "google_oauth.urlopen",
        lambda _request, timeout=None: (llamadas.append(timeout), FakeResponse())[1],
    )

    user = obtener_user_de(FakeCredentials())

    assert user == "lawyer@example.com"
    assert llamadas == [NETWORK_TIMEOUT_S]


def test_obtener_user_de_usa_gmail_profile_si_google_rechaza_userinfo(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout=None):
        assert timeout == NETWORK_TIMEOUT_S
        if request.full_url.endswith("/userinfo"):
            raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=None)
        if request.full_url.endswith("/profile"):
            return FakeResponse({"emailAddress": "lawyer@firm.com.ar"})
        raise AssertionError(f"URL inesperada: {request.full_url}")

    monkeypatch.setattr("google_oauth.urlopen", fake_urlopen)
    monkeypatch.setattr("google_oauth.refrescar_credentials", lambda credentials: None)

    user = obtener_user_de(FakeCredentials())

    assert user == "lawyer@firm.com.ar"


def test_obtener_user_de_informa_error_de_red_con_mensaje_claro(monkeypatch):
    monkeypatch.setattr(
        "google_oauth.urlopen",
        lambda _request, timeout=None: (_ for _ in ()).throw(URLError("offline")),
    )

    try:
        obtener_user_de(FakeCredentials())
    except GoogleOAuthRedError as error:
        assert "No se pudo conectar con Google" in str(error)
        assert "perfil basico de Google" in str(error)
    else:
        assert False, "obtener_user_de deberia informar un error de red"


def test_obtener_user_de_informa_rechazo_de_credenciales_si_fallan_ambos_endpoints(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=None)

    monkeypatch.setattr("google_oauth.urlopen", fake_urlopen)
    monkeypatch.setattr("google_oauth.refrescar_credentials", lambda credentials: None)

    try:
        obtener_user_de(FakeCredentials())
    except GoogleOAuthCredencialesRechazadasError as error:
        assert "perfil basico" in str(error)
        assert "perfil de Gmail" in str(error)
    else:
        assert False, "obtener_user_de deberia informar rechazo de credenciales"


def test_ruta_de_client_secret_detecta_el_nombre_descargado_por_google(monkeypatch):
    with TemporaryDirectory() as directory:
        directorio = Path(directory)
        archivo = directorio / "app_config" / "client_secret_demo.json"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text("{}", encoding="utf-8")

        monkeypatch.delenv("BREAKINGDOWN_GOOGLE_CLIENT_SECRETS_FILE", raising=False)
        monkeypatch.setattr("google_oauth.__file__", str(directorio / "google_oauth.py"))
        monkeypatch.setattr("google_oauth.sys.executable", str(directorio / "python3"))
        monkeypatch.delattr("google_oauth.sys._MEIPASS", raising=False)

        assert ruta_de_client_secret() == archivo


def test_ruta_de_client_secret_prefiere_google_client_secret_en_app_config(monkeypatch):
    with TemporaryDirectory() as directory:
        directorio = Path(directory)
        archivo = directorio / "app_config" / "google_client_secret.json"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text("{}", encoding="utf-8")

        monkeypatch.delenv("BREAKINGDOWN_GOOGLE_CLIENT_SECRETS_FILE", raising=False)
        monkeypatch.setattr("google_oauth.__file__", str(directorio / "google_oauth.py"))
        monkeypatch.setattr("google_oauth.sys.executable", str(directorio / "python3"))
        monkeypatch.delattr("google_oauth.sys._MEIPASS", raising=False)

        assert ruta_de_client_secret() == archivo


def test_ruta_de_client_secret_devuelve_el_primer_candidato_si_hay_multiples(monkeypatch):
    candidatos = [Path("/tmp/uno.json"), Path("/tmp/dos.json")]
    monkeypatch.setattr("google_oauth.rutas_candidatas_de_client_secret", lambda: candidatos)

    assert ruta_de_client_secret() == candidatos[0]


def test_scopes_usan_el_scope_canonico_de_google():
    assert CANONICAL_EMAIL_SCOPE in SCOPES
    assert LEGACY_EMAIL_SCOPE not in SCOPES


def test_ruta_de_configuracion_usa_xdg_en_linux(monkeypatch):
    monkeypatch.setattr("google_oauth.sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg-config")
    monkeypatch.delenv("BREAKINGDOWN_CONFIG_DIR", raising=False)

    assert ruta_de_configuracion() == Path("/tmp/xdg-config") / APP_NAME


def test_ruta_de_token_usa_el_directorio_de_configuracion(monkeypatch):
    monkeypatch.setattr("google_oauth.ruta_de_configuracion", lambda: Path("/tmp/config-dir"))
    monkeypatch.delenv("BREAKINGDOWN_GOOGLE_TOKEN_FILE", raising=False)

    assert ruta_de_token() == Path("/tmp/config-dir") / "google_oauth_token.json"


def test_cargar_credentials_guardadas_reintenta_con_scope_legacy(monkeypatch):
    class FakeCredentialsLoader:
        calls = []

        @classmethod
        def from_authorized_user_file(cls, path, scopes):
            cls.calls.append((path, list(scopes)))
            if scopes == SCOPES:
                raise ValueError("scope mismatch")
            return {"path": path, "scopes": list(scopes)}

    monkeypatch.setattr(
        "google_oauth.imports_de_google",
        lambda: (object(), FakeCredentialsLoader, object()),
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        path.write_text("{}", encoding="utf-8")

        credentials = cargar_credentials_guardadas(path)

    assert credentials == {
        "path": str(path),
        "scopes": ["openid", LEGACY_EMAIL_SCOPE, "https://mail.google.com/"],
    }
    assert FakeCredentialsLoader.calls == [
        (str(path), SCOPES),
        (str(path), ["openid", LEGACY_EMAIL_SCOPE, "https://mail.google.com/"]),
    ]


def test_borrar_credentials_guardadas_elimina_el_archivo():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        path.write_text("{}", encoding="utf-8")

        borrar_credentials_guardadas(path)

        assert path.exists() is False


def test_guardar_credentials_informa_la_ruta_si_falla_la_escritura(monkeypatch):
    credentials = FakeCredentials()

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        monkeypatch.setattr(Path, "write_text", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("denied")))

        try:
            guardar_credentials(credentials, path)
        except Exception as error:
            assert str(path) in str(error)
        else:
            assert False, "guardar_credentials deberia haber fallado"


def test_cargar_sesion_guardada_devuelve_none_si_no_hay_token(monkeypatch):
    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        monkeypatch.setattr("google_oauth.ruta_de_token", lambda: path)

        assert cargar_sesion_guardada() is None


def test_iniciar_sesion_forzada_borra_el_token_y_crea_una_sesion_nueva(monkeypatch):
    credenciales_nuevas = FakeCredentials(token="token-nuevo")

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"
        path.write_text('{"token": "token-viejo"}', encoding="utf-8")

        monkeypatch.setattr("google_oauth.ruta_de_token", lambda: path)
        monkeypatch.setattr("google_oauth.cargar_sesion_guardada", lambda: None)
        monkeypatch.setattr(
            "google_oauth.flujo_local_desde_client_secret",
            lambda _path, prompt=None: credenciales_nuevas,
        )
        monkeypatch.setattr(
            "google_oauth.ruta_de_client_secret",
            lambda: Path(directory) / "google_client_secret.json",
        )
        monkeypatch.setattr(
            "google_oauth.obtener_user_de",
            lambda credentials: "lawyer@example.com",
        )

        sesion = iniciar_sesion(forzar_nueva=True)

        assert sesion.user == "lawyer@example.com"
        assert path.read_text(encoding="utf-8") == credenciales_nuevas.to_json()


def test_iniciar_sesion_no_guarda_el_token_si_falla_obtener_el_usuario(monkeypatch):
    credenciales_nuevas = FakeCredentials(token="token-nuevo")

    with TemporaryDirectory() as directory:
        path = Path(directory) / "token.json"

        monkeypatch.setattr("google_oauth.ruta_de_token", lambda: path)
        monkeypatch.setattr("google_oauth.cargar_sesion_guardada", lambda: None)
        monkeypatch.setattr(
            "google_oauth.flujo_local_desde_client_secret",
            lambda _path, prompt=None: credenciales_nuevas,
        )
        monkeypatch.setattr(
            "google_oauth.ruta_de_client_secret",
            lambda: Path(directory) / "google_client_secret.json",
        )
        monkeypatch.setattr(
            "google_oauth.obtener_user_de",
            lambda credentials: (_ for _ in ()).throw(RuntimeError("userinfo failed")),
        )

        try:
            iniciar_sesion()
        except RuntimeError as error:
            assert str(error) == "userinfo failed"
        else:
            assert False, "iniciar_sesion deberia haber fallado"

        assert path.exists() is False
