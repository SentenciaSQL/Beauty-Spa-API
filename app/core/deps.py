from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import Request
from app.core.audit_context import current_actor_user_id
from app.core.db import get_db
from app.core.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise JWTError("missing sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # request.state.user_id = user.id
    # current_actor_user_id.set(user.id)
    db.info["actor_user_id"] = user.id

    return user

def require_roles(*roles: str):
    def _guard(user: User = Depends(get_current_user)) -> User:
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        if user_role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _guard
