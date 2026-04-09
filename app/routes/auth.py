from fastapi import APIRouter, Depends, HTTPException
from app.middleware.schemas import LoginSchema
from app.middleware.auth import create_token, get_current_user
from app.models.user_model import UserModel

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(body: LoginSchema):
    user = UserModel.find_by_email(body.email)
    if not user or not UserModel.verify_password(body.password, user["password_hash"]):
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
            "role":  user["role"]
        }
    }

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
