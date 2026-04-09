"""
record_routes.py — Financial record CRUD endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.middleware.auth import get_current_user, require_role
from app.middleware.schemas import CreateRecordRequest, UpdateRecordRequest
from app.models import record_model

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.get("/")
def list_records(
    type:       Optional[str] = Query(None, pattern="^(income|expense)$"),
    category:   Optional[str] = None,
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date:   Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    page:       int = Query(1, ge=1),
    limit:      int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    return record_model.find_all(
        type=type, category=category,
        start_date=start_date, end_date=end_date,
        page=page, limit=limit,
    )


@router.get("/{record_id}")
def get_record(record_id: str, _: dict = Depends(get_current_user)):
    record = record_model.find_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"record": record}


@router.post("/", status_code=201)
def create_record(
    body: CreateRecordRequest,
    current_user: dict = Depends(require_role("analyst")),
):
    record = record_model.create_record(
        amount=body.amount, type=body.type,
        category=body.category, date=body.date,
        notes=body.notes, created_by=current_user["id"],
    )
    return {"record": record}


@router.patch("/{record_id}")
def update_record(
    record_id: str,
    body: UpdateRecordRequest,
    _: dict = Depends(require_role("analyst")),
):
    if not record_model.find_by_id(record_id):
        raise HTTPException(status_code=404, detail="Record not found")

    updated = record_model.update_record(
        record_id,
        amount=body.amount, type=body.type,
        category=body.category, date=body.date, notes=body.notes,
    )
    return {"record": updated}


@router.delete("/{record_id}")
def delete_record(
    record_id: str,
    _: dict = Depends(require_role("admin")),
):
    if not record_model.find_by_id(record_id):
        raise HTTPException(status_code=404, detail="Record not found")

    record_model.soft_delete(record_id)
    return {"message": "Record deleted successfully"}
