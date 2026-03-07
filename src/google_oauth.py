import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from requests import Session
from requests.exceptions import RequestException

try:
    from google.auth.exceptions import RefreshError
except ModuleNotFoundError:
    RefreshError = Exception

try:
    from src.errores import (
        ConfiguracionGoogleOAuthError,
        GoogleOAuthCredencialesRechazadasError,
        GoogleOAuthError,
        GoogleOAuthRedError,
        GoogleOAuthRespuestaInvalidaError,
    )
except ModuleNotFoundError:
    from errores import (
        ConfiguracionGoogleOAuthError,
        GoogleOAuthCredencialesRechazadasError,
        GoogleOAuthError,
        GoogleOAuthRedError,
        GoogleOAuthRespuestaInvalidaError,
    )


CANONICAL_EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
LEGACY_EMAIL_SCOPE = "email"
SCOPES = [
    "openid",
    CANONICAL_EMAIL_SCOPE,
    "https://mail.google.com/",
]
APP_NAME = "breakingdown"
CLIENT_SECRETS_ENV = "BREAKINGDOWN_GOOGLE_CLIENT_SECRETS_FILE"
CONFIG_DIR_ENV = "BREAKINGDOWN_CONFIG_DIR"
TOKEN_FILE_ENV = "BREAKINGDOWN_GOOGLE_TOKEN_FILE"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
NETWORK_TIMEOUT_S = 15


class SessionConTimeout(Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", NETWORK_TIMEOUT_S)
        return super().request(*args, **kwargs)


def directorios_base_para_client_secret():
    directorios = []

    if getattr(sys, "_MEIPASS", None):
        directorios.append(Path(sys._MEIPASS))

    directorios.append(Path(__file__).resolve().parent)
    directorios.append(Path(sys.executable).resolve().parent)

    vistos = []
    for directorio in directorios:
        if directorio not in vistos:
            vistos.append(directorio)
    return vistos


def rutas_candidatas_de_client_secret():
    ruta = os.environ.get(CLIENT_SECRETS_ENV)
    if ruta:
        return [Path(ruta).expanduser()]

    candidatos = []
    for directorio in directorios_base_para_client_secret():
        candidatos.append(directorio / "app_config" / "google_client_secret.json")
        candidatos.append(directorio / "google_client_secret.json")

    for candidato in candidatos:
        if candidato.exists():
            return [candidato]

    descargados = []
    for directorio in directorios_base_para_client_secret():
        descargados.extend(sorted((directorio / "app_config").glob("client_secret_*.json")))
        descargados.extend(sorted(directorio.glob("client_secret_*.json")))

    vistos = []
    for candidato in descargados:
        if candidato not in vistos:
            vistos.append(candidato)
    return vistos


def ruta_de_client_secret():
    candidatos = rutas_candidatas_de_client_secret()
    if candidatos:
        return candidatos[0]
    return Path(__file__).resolve().parent / "app_config" / "google_client_secret.json"


def ruta_de_configuracion():
    ruta = os.environ.get(CONFIG_DIR_ENV)
    if ruta:
        return Path(ruta).expanduser()

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata).expanduser() / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / APP_NAME

    return Path.home() / ".config" / APP_NAME


def ruta_de_token():
    ruta = os.environ.get(TOKEN_FILE_ENV)
    if ruta:
        return Path(ruta).expanduser()
    return ruta_de_configuracion() / "google_oauth_token.json"


def imports_de_google():
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ModuleNotFoundError as error:
        raise ConfiguracionGoogleOAuthError(
            "Faltan dependencias de Google OAuth. Instale google-auth y google-auth-oauthlib."
        ) from error

    return GoogleRequest, Credentials, InstalledAppFlow


def construir_google_request():
    GoogleRequest, _, _ = imports_de_google()
    session = SessionConTimeout()
    return GoogleRequest(session=session), session


@dataclass
class SesionGoogleOAuth:
    user: str
    credentials: object
    token_path: Path

    def access_token(self):
        self.refrescar_si_es_necesario()
        return self.credentials.token

    def refrescar(self):
        if not getattr(self.credentials, "refresh_token", None):
            raise GoogleOAuthError(
                "La sesion de Google expiro y no tiene refresh token para renovarse."
            )

        google_request, session = construir_google_request()
        try:
            self.credentials.refresh(google_request)
        except RequestException as error:
            raise GoogleOAuthRedError(
                "No se pudo conectar con Google para refrescar la sesion OAuth."
            ) from error
        except RefreshError as error:
            raise GoogleOAuthCredencialesRechazadasError(
                "Google rechazo las credenciales OAuth al intentar refrescar la sesion."
            ) from error
        finally:
            session.close()
        guardar_credentials(self.credentials, self.token_path)

    def refrescar_si_es_necesario(self):
        if getattr(self.credentials, "valid", False):
            return
        self.refrescar()


def guardar_credentials(credentials, token_path):
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    except OSError as error:
        raise GoogleOAuthError(
            "No se pudo guardar la sesion de Google en "
            f"{token_path}."
        ) from error


def refrescar_credentials(credentials):
    if not getattr(credentials, "refresh_token", None):
        raise GoogleOAuthCredencialesRechazadasError(
            "Google rechazo las credenciales OAuth y la sesion no tiene refresh token para renovarse."
        )

    google_request, session = construir_google_request()
    try:
        credentials.refresh(google_request)
    except RequestException as error:
        raise GoogleOAuthRedError(
            "No se pudo conectar con Google para refrescar las credenciales OAuth."
        ) from error
    except RefreshError as error:
        raise GoogleOAuthCredencialesRechazadasError(
            "Google rechazo las credenciales OAuth al intentar refrescarlas."
        ) from error
    finally:
        session.close()


def leer_json_de_google(credentials, url, descripcion):
    request = Request(
        url,
        headers={"Authorization": f"Bearer {credentials.token}"},
    )
    try:
        with urlopen(request, timeout=NETWORK_TIMEOUT_S) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code in (401, 403):
            raise GoogleOAuthCredencialesRechazadasError(
                f"Google rechazo las credenciales OAuth al consultar {descripcion} (HTTP {error.code})."
            ) from error
        raise GoogleOAuthError(
            f"Google devolvio un error inesperado al consultar {descripcion} (HTTP {error.code})."
        ) from error
    except URLError as error:
        raise GoogleOAuthRedError(
            f"No se pudo conectar con Google al consultar {descripcion}. Revise la conexion e intente nuevamente."
        ) from error
    except json.JSONDecodeError as error:
        raise GoogleOAuthRespuestaInvalidaError(
            f"Google devolvio una respuesta invalida al consultar {descripcion}."
        ) from error


def obtener_email_desde_payload(payload, campo, descripcion):
    user = payload.get(campo, "").strip()
    if not user:
        raise GoogleOAuthRespuestaInvalidaError(
            f"Google respondio sin un correo util al consultar {descripcion}."
        )
    return user


def consultar_correo_de_google(credentials, url, campo, descripcion):
    intento_de_refresh = False

    while True:
        try:
            payload = leer_json_de_google(credentials, url, descripcion)
            return obtener_email_desde_payload(payload, campo, descripcion)
        except GoogleOAuthCredencialesRechazadasError:
            if intento_de_refresh:
                raise
            refrescar_credentials(credentials)
            intento_de_refresh = True


def cargar_credentials_guardadas(token_path):
    if not token_path.exists():
        return None

    _, Credentials, _ = imports_de_google()
    for scopes in (
        SCOPES,
        ["openid", LEGACY_EMAIL_SCOPE, "https://mail.google.com/"],
    ):
        try:
            return Credentials.from_authorized_user_file(str(token_path), scopes)
        except ValueError:
            continue
    return Credentials.from_authorized_user_file(str(token_path), SCOPES)


def borrar_credentials_guardadas(token_path=None):
    token_path = token_path or ruta_de_token()
    token_path.unlink(missing_ok=True)


def obtener_user_de(credentials):
    try:
        return consultar_correo_de_google(
            credentials,
            USERINFO_URL,
            "email",
            "el perfil basico de Google",
        )
    except GoogleOAuthCredencialesRechazadasError as error_de_userinfo:
        try:
            return consultar_correo_de_google(
                credentials,
                GMAIL_PROFILE_URL,
                "emailAddress",
                "el perfil de Gmail",
            )
        except GoogleOAuthCredencialesRechazadasError as error_de_gmail:
            raise GoogleOAuthCredencialesRechazadasError(
                "Google rechazo las credenciales OAuth al consultar tanto el perfil basico como el perfil de Gmail. "
                "Reintente OAuth o use otra cuenta."
            ) from error_de_gmail
        except GoogleOAuthRespuestaInvalidaError:
            raise GoogleOAuthRespuestaInvalidaError(
                "Google respondio sin un correo usable en el perfil de Gmail despues de rechazar el perfil basico."
            ) from error_de_userinfo
    except GoogleOAuthRespuestaInvalidaError:
        return consultar_correo_de_google(
            credentials,
            GMAIL_PROFILE_URL,
            "emailAddress",
            "el perfil de Gmail",
        )


def construir_sesion(credentials, token_path, guardar_en_disco=False):
    sesion = SesionGoogleOAuth("", credentials, token_path)
    sesion.refrescar_si_es_necesario()
    sesion.user = obtener_user_de(credentials)
    if guardar_en_disco:
        guardar_credentials(credentials, token_path)
    return sesion


def flujo_local_desde_client_secret(client_secret_path, prompt=None):
    GoogleRequest, _, InstalledAppFlow = imports_de_google()

    if not client_secret_path.exists():
        rutas_sugeridas = [str(ruta) for ruta in rutas_candidatas_de_client_secret()]
        detalle = ""
        if rutas_sugeridas:
            detalle = " Se detectaron estas rutas posibles: " + ", ".join(rutas_sugeridas) + "."
        raise ConfiguracionGoogleOAuthError(
            "Falta el archivo de credenciales OAuth de Google. "
            f"Configure {CLIENT_SECRETS_ENV} o cree {client_secret_path}.{detalle}"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        authorization_prompt_message="Abriendo Google en el navegador para iniciar sesion...",
        success_message="La autenticacion termino. Ya puede volver a BreakingDown.",
        open_browser=True,
        prompt=prompt,
    )
    if not getattr(credentials, "valid", False) and getattr(credentials, "refresh_token", None):
        credentials.refresh(GoogleRequest())
    return credentials


def cargar_sesion_guardada():
    token_path = ruta_de_token()
    credentials = cargar_credentials_guardadas(token_path)

    if credentials is None:
        return None

    return construir_sesion(credentials, token_path, guardar_en_disco=True)


def iniciar_sesion(forzar_nueva=False, seleccionar_cuenta=False):
    token_path = ruta_de_token()

    if forzar_nueva:
        borrar_credentials_guardadas(token_path)

    sesion = cargar_sesion_guardada()
    if sesion is not None:
        return sesion

    prompt = "select_account" if seleccionar_cuenta else None
    credentials = flujo_local_desde_client_secret(
        ruta_de_client_secret(),
        prompt=prompt,
    )
    return construir_sesion(credentials, token_path, guardar_en_disco=True)
