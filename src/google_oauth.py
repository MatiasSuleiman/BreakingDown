import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from src.errores import ConfiguracionGoogleOAuthError, GoogleOAuthError
except ModuleNotFoundError:
    from errores import ConfiguracionGoogleOAuthError, GoogleOAuthError


CANONICAL_EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
LEGACY_EMAIL_SCOPE = "email"
SCOPES = [
    "openid",
    CANONICAL_EMAIL_SCOPE,
    "https://mail.google.com/",
]
CLIENT_SECRETS_ENV = "BREAKINGDOWN_GOOGLE_CLIENT_SECRETS_FILE"
TOKEN_FILE_ENV = "BREAKINGDOWN_GOOGLE_TOKEN_FILE"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


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
    if len(candidatos) == 1:
        return candidatos[0]
    return Path(__file__).resolve().parent / "app_config" / "google_client_secret.json"


def ruta_de_token():
    ruta = os.environ.get(TOKEN_FILE_ENV)
    if ruta:
        return Path(ruta).expanduser()
    return Path.home() / ".config" / "breakingdown" / "google_oauth_token.json"


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

        GoogleRequest, _, _ = imports_de_google()
        self.credentials.refresh(GoogleRequest())
        guardar_credentials(self.credentials, self.token_path)

    def refrescar_si_es_necesario(self):
        if getattr(self.credentials, "valid", False):
            return
        self.refrescar()


def guardar_credentials(credentials, token_path):
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")


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
    request = Request(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {credentials.token}"},
    )
    try:
        with urlopen(request) as response:
            payload = json.load(response)
    except URLError as error:
        raise GoogleOAuthError(
            "No se pudo obtener el correo del usuario autenticado en Google."
        ) from error

    user = payload.get("email", "").strip()
    if not user:
        raise GoogleOAuthError("Google no devolvio un correo para la cuenta autenticada.")
    return user


def flujo_local_desde_client_secret(client_secret_path):
    GoogleRequest, _, InstalledAppFlow = imports_de_google()

    if not client_secret_path.exists():
        raise ConfiguracionGoogleOAuthError(
            "Falta el archivo de credenciales OAuth de Google. "
            f"Configure {CLIENT_SECRETS_ENV} o cree {client_secret_path}."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        authorization_prompt_message="Abriendo Google en el navegador para iniciar sesion...",
        success_message="La autenticacion termino. Ya puede volver a BreakingDown.",
        open_browser=True,
    )
    if not getattr(credentials, "valid", False) and getattr(credentials, "refresh_token", None):
        credentials.refresh(GoogleRequest())
    return credentials


def cargar_sesion_guardada():
    token_path = ruta_de_token()
    credentials = cargar_credentials_guardadas(token_path)

    if credentials is None:
        return None

    sesion = SesionGoogleOAuth("", credentials, token_path)
    sesion.refrescar_si_es_necesario()
    sesion.user = obtener_user_de(credentials)
    return sesion


def iniciar_sesion(forzar_nueva=False):
    token_path = ruta_de_token()

    if forzar_nueva:
        borrar_credentials_guardadas(token_path)

    sesion = cargar_sesion_guardada()
    if sesion is not None:
        return sesion

    credentials = flujo_local_desde_client_secret(ruta_de_client_secret())
    guardar_credentials(credentials, token_path)

    sesion = SesionGoogleOAuth("", credentials, token_path)
    sesion.refrescar_si_es_necesario()
    sesion.user = obtener_user_de(credentials)
    return sesion
