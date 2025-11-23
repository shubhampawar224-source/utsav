import os
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-secret")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

_signer = URLSafeSerializer(SECRET_KEY, salt="session")


def create_session_token(username: str) -> str:
    return _signer.dumps({"user": username})


def verify_session_token(token: str) -> str:
    try:
        data = _signer.loads(token)
        return data.get("user")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")


def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("session")
    if not token:
        return False
    try:
        user = verify_session_token(token)
    except HTTPException:
        return False
    return user == ADMIN_USER
