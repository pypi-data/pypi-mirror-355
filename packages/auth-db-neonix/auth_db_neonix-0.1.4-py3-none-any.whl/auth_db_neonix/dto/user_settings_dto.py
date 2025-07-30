from ..models.settings_base_class import SettingsBaseClass, SettingsTypeEnum as TypeEnum


# TODO: Validate paths (e.g., check if files exist, or match expected format)
class DbSetting(SettingsBaseClass):
    """
    Setting class for managing database and UI paths.

    Attributes:
        item_db_path (str): Path to the database containing item definitions.
        data_db_path (str): Path to the main data database.
        ui_path (str): Path to the UI layout or configuration file.
    """

    def __init__(
            self,
            item_db_path: str,
            data_db_path: str,
            ui_path: str,
            name: str,
            settings_id: int,
            is_default: bool
    ):
        """
        Initialize DbSetting with path information.

        Args:
            item_db_path (str): File system path to the item database.
            data_db_path (str): File system path to the data database.
            ui_path (str): File system path to the UI settings or template.
            name (str): Descriptive name of the settings.
            settings_id (int): Unique identifier for this settings entry.
            is_default (bool): Whether this is the default settings configuration.
        """
        self.item_db_path = item_db_path
        self.data_db_path = data_db_path
        self.ui_path = ui_path
        super().__init__(TypeEnum.PATH, is_default, name, settings_id)

    def _set_settings(self) -> dict:
        """
        Prepare the dictionary to be stored or exported.

        Returns:
            dict: A dictionary containing all relevant paths.
        """
        return {
            "ITEM_DB_PATH": self.item_db_path,
            "DATA_DB_PATH": self.data_db_path,
            "UI_PPATH": self.ui_path
        }


class SocketSettings(SettingsBaseClass):
    """
    Setting class for defining socket connection parameters.

    Attributes:
        port (int): Port number for the socket connection.
        address (str): IP or hostname of the target socket server.
    """

    def __init__(
            self,
            port: int,
            address: str,
            name: str,
            settings_id: int,
            is_default: bool
    ):
        """
        Initialize socket connection settings.

        Args:
            port (int): Port number.
            address (str): Socket server address.
            name (str): Name of the configuration.
            settings_id (int): Unique settings ID.
            is_default (bool): If this is the default configuration.
        """
        self.port = port
        self.address = address
        super().__init__(TypeEnum.PATH, is_default, name, settings_id)

    def _set_settings(self) -> dict:
        """
        Export settings as dictionary.

        Returns:
            dict: Dictionary containing socket configuration.
        """
        return {
            "PORT": self.port,
            "ADDRESS": self.address
        }
