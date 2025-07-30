from typing import TypedDict


class BaseSettingsDto(TypedDict):
    """
    Data structure representing the base settings configuration for a user.

    Attributes:
        Id (int): Unique identifier for the settings object.
        Type (str): Type of settings (e.g. 'PATH', 'SOCKET', etc.).
        Settings (dict): Dictionary containing the specific configuration values.
        Name (str): Human-readable name for the settings profile.
        Is_Default (bool): Flag indicating whether this is the default settings profile.
    """
    Id: int
    Type: str
    Settings: dict
    Name: str
    Is_Default: bool

