"""
Autenticación JWT mínima para la prueba técnica.

Esto es deliberadamente sencillo: usuarios hardcoded, secret en código.
NO es código de producción; sirve solo para que el frontend tenga contra qué
autenticarse.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = "scm-prueba-tecnica-shared-secret"  # solo para la prueba
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRES_MINUTES = 60
JWT_REFRESH_EXPIRES_DAYS = 7

USERS: dict[str, str] = {
    "admin": "admin",
    "demo": "demo",
}

_bearer = HTTPBearer(auto_error=True)


def authenticate(username: str, password: str) -> bool:
    return USERS.get(username) == password


def _encode(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    return _encode(subject, "access", timedelta(minutes=JWT_ACCESS_EXPIRES_MINUTES))


def create_refresh_token(subject: str) -> str:
    return _encode(subject, "refresh", timedelta(days=JWT_REFRESH_EXPIRES_DAYS))


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def _extract_subject(payload: dict, expected_type: str) -> str:
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin 'sub'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return sub


def decode_refresh_token(token: str) -> str:
    return _extract_subject(_decode(token), "refresh")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    return _extract_subject(_decode(credentials.credentials), "access")
