class CredencialesInvalidasError(Exception):
    pass


class GoogleOAuthError(Exception):
    pass


class ConfiguracionGoogleOAuthError(GoogleOAuthError):
    pass


class GoogleOAuthCredencialesRechazadasError(GoogleOAuthError):
    pass


class GoogleOAuthRedError(GoogleOAuthError):
    pass


class GoogleOAuthRespuestaInvalidaError(GoogleOAuthError):
    pass
