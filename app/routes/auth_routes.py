"""
auth_routes.py — Login and current-user endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.middleware.schemas import LoginRequest
from app.middleware.auth import create_token, get_current_user
from app.models import user_model

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(body: LoginRequest):
    user = user_model.find_by_email(body.email)

    if not user or not user_model.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is inactive. Contact an administrator.")

    token = create_token(user["id"])
    return {
        "token": token,
        "user": {
            "id":    user["id"],
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"],
        },
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
