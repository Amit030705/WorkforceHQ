from datetime import date

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.dependencies import AdminUser, DbSession
from app.models.attendance import Attendance
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(admin: AdminUser, db: DbSession):
    return DashboardStats(
        total_employees=db.scalar(select(func.count(Employee.id))) or 0,
        active_employees=db.scalar(
            select(func.count(Employee.id)).where(Employee.employment_status == "active")
        )
        or 0,
        total_departments=db.scalar(select(func.count(Department.id))) or 0,
        employees_present_today=db.scalar(
            select(func.count(func.distinct(Attendance.employee_id))).where(
                Attendance.attendance_date == date.today(),
                Attendance.status == "present",
            )
        )
        or 0,
        pending_leave_requests=db.scalar(
            select(func.count(LeaveRequest.id)).where(LeaveRequest.status == "pending")
        )
        or 0,
    )

