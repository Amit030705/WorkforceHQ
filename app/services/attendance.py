from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate
from app.services.errors import Conflict, RecordNotFound


def record_attendance(db: Session, payload: AttendanceCreate, recorded_by_id: int) -> Attendance:
    if db.get(Employee, payload.employee_id) is None:
        raise RecordNotFound("Employee not found.")
    entry = Attendance(**payload.model_dump(), recorded_by_id=recorded_by_id)
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("Attendance has already been recorded for this employee on this date.") from exc
    return entry


def attendance_rows_query():
    return (
        select(
            Attendance.id,
            Attendance.employee_id,
            Employee.name.label("employee_name"),
            Attendance.attendance_date,
            Attendance.status,
            Attendance.notes,
            Attendance.recorded_by_id,
            Attendance.created_at,
        )
        .join(Employee)
    )

