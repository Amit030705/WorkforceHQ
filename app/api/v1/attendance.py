from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, AttendanceRead, AttendanceSummary
from app.schemas.common import Page
from app.services.attendance import attendance_rows_query
from app.services.attendance import record_attendance as record_attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def record_attendance(payload: AttendanceCreate, admin: AdminUser, db: DbSession):
    entry = record_attendance_service(db, payload, admin.id)
    row = db.execute(attendance_rows_query().where(Attendance.id == entry.id)).one()
    return dict(row._mapping)


@router.get("", response_model=Page[AttendanceRead])
def list_attendance(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    employee_id: int | None = Query(default=None, gt=0),
    start_date: date | None = None,
    end_date: date | None = None,
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "start_date must be on or before end_date.")
    filters = []
    if user.role != "admin":
        if user.employee is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No employee profile is linked to this account.")
        filters.append(Attendance.employee_id == user.employee.id)
    elif employee_id is not None:
        filters.append(Attendance.employee_id == employee_id)
    if start_date:
        filters.append(Attendance.attendance_date >= start_date)
    if end_date:
        filters.append(Attendance.attendance_date <= end_date)
    total = db.scalar(select(func.count(Attendance.id)).where(*filters)) or 0
    rows = db.execute(
        attendance_rows_query()
        .where(*filters)
        .order_by(Attendance.attendance_date.desc(), Attendance.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[dict(row._mapping) for row in rows], total=total, page=page, page_size=page_size
    )


@router.get("/summary", response_model=AttendanceSummary)
def attendance_summary(
    user: CurrentUser,
    db: DbSession,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: int | None = Query(default=None, gt=0),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "start_date must be on or before end_date.")
    filters = []
    if user.role != "admin":
        if user.employee is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No employee profile is linked to this account.")
        filters.append(Attendance.employee_id == user.employee.id)
    elif employee_id is not None:
        filters.append(Attendance.employee_id == employee_id)
    if start_date:
        filters.append(Attendance.attendance_date >= start_date)
    if end_date:
        filters.append(Attendance.attendance_date <= end_date)
    rows = db.execute(
        select(Attendance.status, func.count(Attendance.id)).where(*filters).group_by(Attendance.status)
    ).all()
    counts = {name: count for name, count in rows}
    return AttendanceSummary(
        present=counts.get("present", 0),
        absent=counts.get("absent", 0),
        late=counts.get("late", 0),
        half_day=counts.get("half_day", 0),
        total=sum(counts.values()),
    )
