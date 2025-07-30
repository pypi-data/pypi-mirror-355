from auth_db_neonix.security.auth import login, signup, signup, verify_cookie_from_module, verify_cookie_from_https
from auth_db_neonix.security.cripto import encrypt, decrypt

from auth_db_neonix.services.fire_client_service import FirebaseClient
from auth_db_neonix.services.sqlite_service import SQLiteManager
from auth_db_neonix.services.data_retriver_service import DataRetriever
from auth_db_neonix.services.firebase_init import firebase_init

from auth_db_neonix.models.user import User
from auth_db_neonix.dto.user_settings_dto import DbSetting
from auth_db_neonix.dto.base_settings_dto import BaseSettingsDto

from auth_db_neonix.version import __version__

from auth_db_neonix import main

# TODOs:
# TODO - Add session management helper for web frameworks (e.g., Flask, FastAPI)
# TODO - Implement caching layer for Firebase reads
# TODO - Add CLI wrapper for auth and settings commands
# TODO - Add function to list all settings for a given user
# TODO - Provide unified exception handling and logging utils

__all__ = [
    "login",
    "signup",
    "verify_cookie_from_module",
    "verify_cookie_from_https",
    "FirebaseClient",
    "SQLiteManager",
    "DataRetriever",
    "User",
    "DbSetting",
    "BaseSettingsDto",
    "encrypt",
    "decrypt",
    "__version__",
    "firebase_init",
    "main"
]
