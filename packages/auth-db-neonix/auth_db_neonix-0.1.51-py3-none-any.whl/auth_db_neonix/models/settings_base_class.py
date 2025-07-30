from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Dict
from ..dto.base_settings_dto import BaseSettingsDto

# ================================
# TODOs:
# TODO - [ ] Implement factory logic in `from_dict` to instantiate the correct subclass
# TODO - [ ] Add validation logic for `settings` using e.g., `pydantic`
# TODO - [ ] Consider serializing/deserializing enums more explicitly
# TODO - [ ] Introduce settings schema registry for better extensibility
# ================================


class SettingsTypeEnum(Enum):
    """Defines the types of settings available."""
    SOCKET = auto()
    PATH = auto()
    CLOUD = auto()
    DOCKER = auto()


class SettingsBaseClass(ABC):
    """
    Abstract base class for all settings types.
    """

    def __init__(
            self,
            setting_type: SettingsTypeEnum,
            is_default: bool,
            name: str,
            settings_id: int,
            settings: Optional[Dict] = None,
    ):
        self._type = setting_type
        self.is_default: bool = is_default
        self._id = settings_id
        self._name = name

        # Use internal constructor logic or external settings
        self._settings: Dict = self._set_settings() if settings is None else settings

    @property
    def get_type(self) -> SettingsTypeEnum:
        """Returns the type of the settings (SOCKET, PATH, etc.)."""
        return self._type

    @property
    def get_settings(self) -> Dict:
        """Returns the actual settings as a dictionary."""
        return self._settings

    @property
    def get_id(self) -> int:
        """Returns the ID of the settings."""
        return self._id

    @property
    def get_name(self) -> str:
        """Returns the name of the settings configuration."""
        return self._name

    @property
    def to_dict(self) -> BaseSettingsDto:
        """Converts the current settings object into a serializable dictionary."""
        return {
            "Id": self._id,
            "Type": str(self._type.value),
            "Settings": self._settings,
            "Name": self._name,
            "Is_Default": self.is_default,
        }

    @abstractmethod
    def _set_settings(self) -> Dict:
        """Subclasses must implement this method to define their setting structure."""
        ...

    @classmethod
    def from_dict(cls, record: dict) -> "SettingsBaseClass":
        """
        Reconstructs a settings object from a dictionary.

        WARNING: This will fail if used with abstract base class directly.
        TODO: Implement factory pattern to return correct subclass based on record["Type"]
        """
        return cls(
            SettingsTypeEnum(record["Type"]),
            record["Is_Default"],
            record["Name"],
            record["Id"],
            record["Settings"],
        )
