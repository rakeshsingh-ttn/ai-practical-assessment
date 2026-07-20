from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.auth.dependencies import get_current_user
from src.backend.app.auth.jwt import create_access_token
from src.backend.app.auth.passwords import verify_password
from src.backend.app.database import get_db
from src.backend.app.exceptions import UnauthorizedError
from src.backend.app.models.entities import User
from src.backend.app.schemas import LoginRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
