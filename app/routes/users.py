from fastapi import APIRouter, Depends, HTTPException, Query
from app.middleware.schemas import CreateUserSchema, UpdateUserSchema
from app.middleware.auth import require_role, get_current_user
from app.models.user_model import UserModel

router = APIRouter(prefix="/users", tags=["Users"])

admin_only = require_role("admin")

@router.get("/")
def list_users(
    status: str = Query(None),
    role:   str = Query(None),
    page:   int = Query(1, ge=1),
    limit:  int = Query(20, ge=1, le=100),
    _: dict = Depends(admin_only)
):
    return UserModel.find_all(status=status, role=role, page=page, limit=limit)

@router.get("/{user_id}")
def get_user(user_id: str, _: dict = Depends(admin_only)):
    user = UserModel.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

@router.post("/", status_code=201)
def create_user(body: CreateUserSchema, _: dict = Depends(admin_only)):
    if UserModel.find_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email is already in use")
    user = UserModel.create(
        name=body.name, email=body.email,
        password=body.password, role=body.role
    )
    return {"user": user}

@router.patch("/{user_id}")
def update_user(
    user_id: str,
    body: UpdateUserSchema,
    current_user: dict = Depends(admin_only)
):
    if not UserModel.find_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == current_user["id"] and body.status == "inactive":
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    updated = UserModel.update(user_id, body.model_dump())
    return {"user": updated}

@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(admin_only)):
    if not UserModel.find_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    UserModel.delete(user_id)
    return {"message": "User deleted successfully"}
