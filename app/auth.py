import os
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-secret")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

_signer = URLSafeSerializer(SECRET_KEY, salt="session")


def create_session_token(payload) -> str:
    """Create a session token. `payload` may be a username string or a dict with keys like
    `user`, `display_name`, `avatar_url`.
    """
    if isinstance(payload, str):
        data = {"user": payload}
    else:
        data = payload
    return _signer.dumps(data)


def verify_session_token(token: str) -> dict:
    """Verify token and return the stored payload as a dict.
    Previously callers expected a username string; updated code should read `data.get('user')`.
    """
    try:
        data = _signer.loads(token)
        if isinstance(data, dict):
            return data
        return {"user": data}
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")


def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("session")
    if not token:
        return False
    try:
        data = verify_session_token(token)
    except HTTPException:
        return False
    user = data.get("user") if isinstance(data, dict) else data
    return user == ADMIN_USER
