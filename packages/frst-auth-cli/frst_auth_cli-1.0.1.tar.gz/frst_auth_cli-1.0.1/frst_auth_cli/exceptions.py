class UserNotFoundError(Exception):
    """Raised when a user cannot be found or token is invalid."""


class GroupNotFoundError(Exception):
    """Raised when a group cannot be found for the user."""


class CompanyNotFoundError(Exception):
    """Raised when a company cannot be found for the user."""


class AppNotFoundError(Exception):
    """Raised when an app cannot be found or token is invalid."""
