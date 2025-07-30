from dotenv import load_dotenv
from cryptography.fernet import Fernet
import os

# region TODOs for future implementations:
# TODO [ ] Log errors instead of printing them (es. con logging module)
# TODO [ ] Raise custom exceptions for missing or invalid keys
# TODO [ ] Aggiungere supporto per rotazione chiavi e versionamento
# TODO [ ] Verificare validità della chiave (lunghezza, base64) prima di usarla
# TODO [ ] Creare un wrapper per criptare/dcriptare interi oggetti o dizionari
# endregion

load_dotenv()


def get_fernet():
    """
    Retrieve the Fernet object using the key from environment variables.
    """
    try:
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY not set in environment")
        return Fernet(key.encode())
    except Exception as ex:
        print(f"Failed to initialize Fernet: {ex}")
        # raise ex  # Uncomment to propagate the error


def encrypt(text: str) -> str:
    """
    Encrypt a string using Fernet.
    """
    return get_fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    """
    Decrypt a Fernet-encrypted string.
    """
    return get_fernet().decrypt(token.encode()).decode()
