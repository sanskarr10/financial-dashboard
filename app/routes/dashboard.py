from fastapi import APIRouter, Depends, Query
from datetime import datetime
from app.middleware.auth import require_role, get_current_user
from app.models.record_model import RecordModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview")
def overview(
    start_date: str = Query(None, alias="startDate"),
    end_date:   str = Query(None, alias="endDate"),
    _: dict = Depends(get_current_user)
):
    return {
        "summary":            RecordModel.get_totals(start_date, end_date),
        "category_breakdown": RecordModel.get_category_totals(start_date=start_date, end_date=end_date),
        "monthly_trends":     RecordModel.get_monthly_trends(datetime.now().year),
        "recent_activity":    RecordModel.get_recent_activity(5),
        "filters":            {"startDate": start_date, "endDate": end_date}
    }

@router.get("/summary")
def summary(
    start_date: str = Query(None, alias="startDate"),
    end_date:   str = Query(None, alias="endDate"),
    _: dict = Depends(get_current_user)
):
    return {
        "summary": RecordModel.get_totals(start_date, end_date),
        "filters": {"startDate": start_date, "endDate": end_date}
    }

@router.get("/recent")
def recent_activity(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(get_current_user)
):
    return {"records": RecordModel.get_recent_activity(limit)}

@router.get("/categories")
def category_breakdown(
    type:       str = Query(None),
    start_date: str = Query(None, alias="startDate"),
    end_date:   str = Query(None, alias="endDate"),
    _: dict = Depends(require_role("analyst"))
):
    categories = RecordModel.get_category_totals(type_=type, start_date=start_date, end_date=end_date)
    grouped = {}
    for row in categories:
        t = row["type"]
        grouped.setdefault(t, []).append({
            "category": row["category"],
            "total":    row["total"],
            "count":    row["count"]
        })
    return {"breakdown": grouped, "filters": {"type": type, "startDate": start_date, "endDate": end_date}}

@router.get("/trends/monthly")
def monthly_trends(
    year: int = Query(None),
    _: dict = Depends(require_role("analyst"))
):
    return {
        "trends": RecordModel.get_monthly_trends(year),
        "year":   year or datetime.now().year
    }

@router.get("/trends/weekly")
def weekly_trends(_: dict = Depends(require_role("analyst"))):
    return {"trends": RecordModel.get_weekly_trends()}
