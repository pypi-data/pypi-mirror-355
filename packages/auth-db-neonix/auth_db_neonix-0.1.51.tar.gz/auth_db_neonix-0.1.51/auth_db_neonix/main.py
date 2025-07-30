from auth_db_neonix import (
    login,
    firebase_init
)


def firebase_start():
    """
    Create Firebase app instance.
    """
    firebase_init()
    log = login(password="Dabbuster88@", email="mia@google.com")
    return log


def test_variables():
    print(firebase_init())


if __name__ == "__main__":
    firebase_start()
