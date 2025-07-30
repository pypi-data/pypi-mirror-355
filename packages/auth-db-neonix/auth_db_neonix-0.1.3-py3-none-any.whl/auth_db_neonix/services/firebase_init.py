import os
import json
import base64
from firebase_admin import credentials, initialize_app
from dotenv import load_dotenv

# ================================
# TODOs:
# TODO - [ ] Allow specifying an alternate path for the .env file as a parameter
# TODO - [ ] Log initialization success/failure (e.g., via logging module)
# TODO - [ ] Validate structure of decoded JSON before passing to Certificate
# TODO - [ ] Add caching to avoid reinitializing the Firebase app
# ================================


def firebase_init():
    """
    Initialize the Firebase app using a base64-encoded service account key.

    Expects the environment variable FIREBASE_CONFIG_B64 to be present,
    which must contain the base64-encoded content of the Firebase admin SDK JSON.
    """
    load_dotenv("auth_db_neonix/.env")

    firebase_b64 = os.getenv("FIREBASE_CONFIG_B64")
    if firebase_b64:
        decoded = base64.b64decode(firebase_b64)
        cred_dict = json.loads(decoded)
        cred = credentials.Certificate(cred_dict)
        initialize_app(cred)
    else:
        raise RuntimeError("Missing FIREBASE_CONFIG_B64 environment variable")
