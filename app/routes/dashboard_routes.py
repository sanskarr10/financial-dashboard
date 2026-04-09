"""
dashboard_routes.py — Analytics and summary endpoints.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from app.middleware.auth import get_current_user, require_role
from app.models import record_model

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def overview(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date:   Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    _: dict = Depends(get_current_user),
):
    """All-in-one endpoint for dashboard initial load."""
    summary    = record_model.get_totals(start_date, end_date)
    categories = record_model.get_category_totals(start_date=start_date, end_date=end_date)
    monthly    = record_model.get_monthly_trends(datetime.now().year)
    recent     = record_model.get_recent_activity(5)
    return {
        "summary":            summary,
        "category_breakdown": categories,
        "monthly_trends":     monthly,
        "recent_activity":    recent,
        "filters":            {"start_date": start_date, "end_date": end_date},
    }


@router.get("/summary")
def summary(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date:   Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    _: dict = Depends(get_current_user),
):
    totals = record_model.get_totals(start_date, end_date)
    return {"summary": totals, "filters": {"start_date": start_date, "end_date": end_date}}


@router.get("/recent")
def recent_activity(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(get_current_user),
):
    return {"records": record_model.get_recent_activity(limit)}


@router.get("/categories")
def category_breakdown(
    type:       Optional[str] = Query(None, pattern="^(income|expense)$"),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date:   Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    _: dict = Depends(require_role("analyst")),
):
    categories = record_model.get_category_totals(type, start_date, end_date)
    grouped: dict = {}
    for row in categories:
        t = row["type"]
        grouped.setdefault(t, []).append({
            "category": row["category"],
            "total":    row["total"],
            "count":    row["count"],
        })
    return {"breakdown": grouped, "filters": {"type": type, "start_date": start_date, "end_date": end_date}}


@router.get("/trends/monthly")
def monthly_trends(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    _: dict = Depends(require_role("analyst")),
):
    target = year or datetime.now().year
    return {"trends": record_model.get_monthly_trends(target), "year": target}


@router.get("/trends/weekly")
def weekly_trends(_: dict = Depends(require_role("analyst"))):
    return {"trends": record_model.get_weekly_trends()}
