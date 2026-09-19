"""Authentication route definitions.
Provides user registration and login, returning JWT access tokens.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import db_dependency
from app.repositories.user import UserRepository
from app.util.security import hash_password, verify_password
from app.util.jwt import create_access_token
from app.core.config import settings
from app.schemas.user import UserCreate as RegisterRequest, Token as LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, conn=Depends(db_dependency)):
    repo = UserRepository(conn)
    existing = repo.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    pwd_hash = hash_password(request.password)
    user = repo.create_user(email=request.email, password_hash=pwd_hash, name=request.name)
    return UserResponse(id=str(user["id"]), email=user["email"], name=user.get("name"))

@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), conn=Depends(db_dependency)):
    repo = UserRepository(conn)
    user = repo.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        # Generic error to avoid user enumeration
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=int(settings.access_token_expire_minutes))
    access_token = create_access_token(data={"sub": str(user["id"]), "email": user["email"]}, expires_delta=access_token_expires)
    return LoginResponse(access_token=access_token, token_type="bearer")


from app.api.dependencies.auth import get_current_user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user), conn=Depends(db_dependency)):
    repo = UserRepository(conn)
    user = repo.get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=str(user["id"]), email=user["email"], name=user.get("name"))
