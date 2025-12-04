"""
Exceptions métier pour Orange Money.
"""


class OrangeMoneyError(Exception):
    """Erreur applicative générique Orange Money."""
    pass


class OrangeMoneyAuthError(OrangeMoneyError):
    """Erreur d'authentification OAuth Orange Money."""
    pass


class OrangeMoneyAPIError(OrangeMoneyError):
    """Erreur lors d'un appel API Orange Money."""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class OrangeMoneyConfigurationError(OrangeMoneyError):
    """Erreur de configuration Orange Money (variables d'environnement manquantes)."""
    pass

