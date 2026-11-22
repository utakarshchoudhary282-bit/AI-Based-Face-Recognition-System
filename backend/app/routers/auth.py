"""POST /api/auth/login (user ID + password -> token) and GET /api/auth/me."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import User, get_db
from ..security import create_token, get_current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["login"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == form.username.strip()).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect user ID or password.")
    return {"access_token": create_token(user), "token_type": "bearer",
            "user_id": user.user_id, "full_name": user.full_name, "role": user.role}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "full_name": user.full_name, "role": user.role}
