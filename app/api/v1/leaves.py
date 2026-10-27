from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.schemas.common import Page
from app.schemas.leave_request import LeaveCreate, LeaveRead, LeaveReview
from app.services.leaves import leave_query, review_leave as review_leave_service
from app.services.leaves import submit_leave as submit_leave_service

router = APIRouter(prefix="/leave-requests", tags=["Leave requests"])


def serialize_leave(item: LeaveRequest) -> dict:
    return {
        "id": item.id,
        "employee_id": item.employee_id,
        "employee_name": item.employee.name,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "reason": item.reason,
        "status": item.status,
        "reviewed_at": item.reviewed_at,
        "reviewer_id": item.reviewer_id,
        "reviewer_email": item.reviewer.email if item.reviewer else None,
        "reviewer_comment": item.reviewer_comment,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.post("", response_model=LeaveRead, status_code=status.HTTP_201_CREATED)
def submit_leave(payload: LeaveCreate, user: CurrentUser, db: DbSession):
    employee = user.employee
    if employee is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No employee profile is linked to this account.")
    item = submit_leave_service(db, employee.id, payload)
    return serialize_leave(item)


@router.get("", response_model=Page[LeaveRead])
def list_leave_requests(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_status: str | None = Query(default=None, alias="status", pattern="^(pending|approved|rejected)$"),
):
    filters = []
    if user.role != "admin":
        if user.employee is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No employee profile is linked to this account.")
        filters.append(LeaveRequest.employee_id == user.employee.id)
    if request_status:
        filters.append(LeaveRequest.status == request_status)
    total = db.scalar(select(func.count(LeaveRequest.id)).where(*filters)) or 0
    items = db.scalars(
        leave_query()
        .where(*filters)
        .order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return Page(
        items=[serialize_leave(item) for item in items], total=total, page=page, page_size=page_size
    )


@router.patch("/{request_id}", response_model=LeaveRead)
def review_leave_request(request_id: int, payload: LeaveReview, admin: AdminUser, db: DbSession):
    item = review_leave_service(db, request_id, payload, admin.id)
    return serialize_leave(item)
