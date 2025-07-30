import requests
import os
from dotenv import load_dotenv
from fastapi import Response, Request
from datetime import timedelta
from firebase_admin import auth

# region TODOs for future implementations:
# TODO [ ] Handle error responses from Firebase more gracefully (e.g., log and return status codes)
# TODO [ ] Add optional retry logic for network errors
# TODO [ ] Abstract Firebase REST logic into a service class or adapter
# TODO [ ] Allow session duration to be configurable via environment variable
# TODO [ ] Add user deletion and password reset functions
# TODO [ ] Add rate limiting or basic throttle to login/signup to prevent abuse
# TODO [ ] Add middleware to enforce authentication in protected routes
# endregion

load_dotenv("auth_db_neonix/.env")
API_KEY = os.getenv("FIREBASE_API_KEY")


def signup(email: str, password: str) -> dict:
    """
    Sign up a user using Firebase REST API.
    Returns response JSON from Firebase.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()


def login(email: str, password: str) -> dict:
    """
    Log in a user using Firebase REST API.
    Returns response JSON with ID token if successful.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()


def create_session_container(id_token: str) -> bytes:
    """
    Create a session cookie from a Firebase ID token.
    The cookie is valid for 3 days.
    """
    expire_delta_time = timedelta(days=3)
    return auth.create_session_cookie(id_token, expire_delta_time)


def verify_cookie_from_https(req: Request) -> tuple[str, bool, str | None]:
    """
    Verify session cookie from incoming HTTPS request.
    Returns the cookie, validity, and user ID if present.
    """
    cookie = req.cookies.get("session")
    valid = False
    user_id = None

    try:
        decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
        user_id = decoded_claims["uid"]
        valid = True
    except Exception as ex:
        print(ex)
        valid = False
    finally:
        return cookie, valid, user_id


def verify_cookie_from_module(cookie: bytes) -> tuple[bytes, bool, str | None]:
    """
    Verify session cookie passed as a parameter.
    Returns the cookie, validity, and user ID if present.
    """
    valid = False
    user_id = None

    try:
        decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
        user_id = decoded_claims["uid"]
        valid = True
    except Exception as ex:
        print(ex)
        valid = False
    finally:
        return cookie, valid, user_id


def generate_api_secure_cookie(session_cookie: bytes) -> Response:
    """
    Generate a FastAPI Response object with a secure session cookie attached.
    """
    response = Response()
    response.set_cookie(
        key="session",
        value=str(session_cookie),
        max_age=3 * 60 * 24,  # 3 days in minutes
        secure=True,
        httponly=True,
        samesite="strict"
    )
    return response
