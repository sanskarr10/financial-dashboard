"""
user_routes.py — User management endpoints (admin only).
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.middleware.auth import require_role
from app.middleware.schemas import CreateUserRequest, UpdateUserRequest
from app.models import user_model

router = APIRouter(prefix="/users", tags=["User Management"])

# All user routes require admin
AdminOnly = Depends(require_role("admin"))


@router.get("/")
def list_users(
    status: Optional[str] = Query(None, pattern="^(active|inactive)$"),
    role:   Optional[str] = Query(None, pattern="^(viewer|analyst|admin)$"),
    page:   int = Query(1, ge=1),
    limit:  int = Query(20, ge=1, le=100),
    _=AdminOnly,
):
    return user_model.find_all(status=status, role=role, page=page, limit=limit)


@router.get("/{user_id}")
def get_user(user_id: str, _=AdminOnly):
    user = user_model.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}


@router.post("/", status_code=201)
def create_user(body: CreateUserRequest, _=AdminOnly):
    if user_model.find_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email is already in use")
    user = user_model.create_user(
        name=body.name, email=body.email,
        password=body.password, role=body.role,
    )
    return {"user": user}


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: dict = Depends(require_role("admin")),
):
    if not user_model.find_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user["id"] and body.status == "inactive":
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    updated = user_model.update_user(
        user_id,
        name=body.name,
        role=body.role,
        status=body.status,
    )
    return {"user": updated}


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    if not user_model.find_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user_model.delete_user(user_id)
    return {"message": "User deleted successfully"}
