from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database import get_db
from src.backend.app.models.entities import User
from src.backend.app.schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.execute(select(User).order_by(User.name)).scalars().all()
    return users
