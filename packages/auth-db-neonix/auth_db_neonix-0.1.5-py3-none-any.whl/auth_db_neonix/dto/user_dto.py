class User_Dto():
    """
   Data Transfer Object (DTO) representing a user with optional settings.

   Attributes:
       profile (dict): Dictionary containing basic user information such as username and email.
       userId (str): Unique identifier for the user (e.g., UID from Firebase).
       settings (Optional[dict]): Optional dictionary containing user settings.
   """
    def __init__(self, username, email, userid, settings=None):
        """
        Initialize a new User_Dto.

        Args:
            username (str): The user's display name.
            email (str): The user's email address.
            userid (str): The user's unique identifier.
            settings (Optional[dict], optional): A dictionary of user settings. Defaults to None.
        """
        self.profile: dict = {"Username": username, "Email": email}
        self.userId = userid
        self.settings = settings

 