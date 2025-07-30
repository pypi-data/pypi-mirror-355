# region TODOs for future implementations:
# TODO [ ] Add validation logic for socket field (IP/port format)
# TODO [ ] Integrate with user ID mapping or foreign key reference
# TODO [ ] Implement __repr__ or __str__ for better debugging
# TODO [ ] Add from_dict and to_dict methods for serialization
# TODO [ ] Include optional metadata (e.g., creation date, version)
# endregion

class User_setting:
    """
    Represents individual user settings, such as socket configuration and user linkage.
    """

    def __init__(self):
        self.socket: str = None
        """Socket address or identifier for this setting (e.g., '127.0.0.1:8080')."""

        self.userId: str = None
        """Associated user ID (typically matches Firebase UID)."""



