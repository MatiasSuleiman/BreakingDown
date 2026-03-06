class CredencialesInvalidasError(Exception):
    pass


class GoogleOAuthError(Exception):
    pass


class ConfiguracionGoogleOAuthError(GoogleOAuthError):
    pass
