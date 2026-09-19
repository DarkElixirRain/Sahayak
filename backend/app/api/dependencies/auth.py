"""Authentication dependencies for FastAPI.
Provides get_current_user which validates JWT token from Authorization header.
"""

from typing import Optional

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import settings

def _decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

def get_current_user(request: Request) -> dict:
    """Extract and validate JWT token, returning user info.
    Returns a dict with at least 'id' and 'email'.
    """
    auth: Optional[str] = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth[7:]
    payload = _decode_jwt(token)
    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user_id, "email": email, "name": payload.get("name")}
