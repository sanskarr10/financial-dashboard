from fastapi import APIRouter, Depends, HTTPException, Query
from app.middleware.schemas import CreateRecordSchema, UpdateRecordSchema
from app.middleware.auth import require_role, get_current_user
from app.models.record_model import RecordModel

router = APIRouter(prefix="/records", tags=["Records"])

@router.get("/")
def list_records(
    type:       str = Query(None),
    category:   str = Query(None),
    start_date: str = Query(None, alias="startDate"),
    end_date:   str = Query(None, alias="endDate"),
    page:       int = Query(1, ge=1),
    limit:      int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user)
):
    return RecordModel.find_all(
        type_=type, category=category,
        start_date=start_date, end_date=end_date,
        page=page, limit=limit
    )

@router.get("/{record_id}")
def get_record(record_id: str, _: dict = Depends(get_current_user)):
    record = RecordModel.find_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"record": record}

@router.post("/", status_code=201)
def create_record(
    body: CreateRecordSchema,
    current_user: dict = Depends(require_role("analyst"))
):
    record = RecordModel.create(
        amount=body.amount, type_=body.type,
        category=body.category, date=body.date,
        notes=body.notes, created_by=current_user["id"]
    )
    return {"record": record}

@router.patch("/{record_id}")
def update_record(
    record_id: str,
    body: UpdateRecordSchema,
    _: dict = Depends(require_role("analyst"))
):
    if not RecordModel.find_by_id(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
    updated = RecordModel.update(record_id, body.model_dump())
    return {"record": updated}

@router.delete("/{record_id}")
def delete_record(
    record_id: str,
    _: dict = Depends(require_role("admin"))
):
    if not RecordModel.find_by_id(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
    RecordModel.soft_delete(record_id)
    return {"message": "Record deleted successfully"}
