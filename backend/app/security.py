"""Login: passwords are stored as bcrypt hashes; a signed JWT token proves who is calling."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import User, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user.user_id, "role": user.role, "exp": expires},
                      settings.JWT_SECRET, algorithm="HS256")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Runs before every protected endpoint: reads the token and finds the user."""
    try:
        user_id = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Please sign in again.")
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(401, "Please sign in again.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin access required.")
    return user


def ensure_default_admin(db: Session):
    """Create the first admin account (from .env) when the database is empty."""
    if db.query(User).count() == 0:
        db.add(User(user_id=settings.ADMIN_USER_ID, full_name="Portal Administrator",
                    password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin"))
        db.commit()
