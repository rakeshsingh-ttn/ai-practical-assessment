from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.backend.app.auth.jwt import decode_access_token
from src.backend.app.database import get_db
from src.backend.app.exceptions import UnauthorizedError
from src.backend.app.models.entities import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication required")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise UnauthorizedError("Invalid or expired token") from None

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")
    return user
