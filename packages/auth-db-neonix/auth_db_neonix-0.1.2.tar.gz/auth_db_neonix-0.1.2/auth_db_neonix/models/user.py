from .user_setting import User_setting
from datetime import datetime

# region TODOs for future implementations:
# TODO [ ] Add validation logic for profile fields (username, email)
# TODO [ ] Implement methods to serialize/deserialize user data
# TODO [ ] Handle JWT and refresh token expiration automatically
# TODO [ ] Add method to load/save user settings from external source
# TODO [ ] Consider converting to a dataclass for simplicity
# endregion


class User:
    """
    Represents a user object with profile info, authentication tokens, and settings.
    """

    def __init__(self):
        self.profile: dict = {"Username": None, "Email": None}
        """User profile information as dictionary."""

        self.userId: str = None
        """Unique user identifier (Firebase UID)."""

        self.jwt: str = None
        """JWT (ID token) returned by Firebase during login."""

        self.j_refresh_token: str = None
        """Refresh token returned by Firebase."""

        self.j_expiration_datetime: datetime = None
        """Datetime when the JWT expires."""

        self.settings: list[User_setting] = []
        """List of user-specific settings objects."""
