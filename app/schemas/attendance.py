from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import ORMModel


class AttendanceCreate(ORMModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    status: Literal["present", "absent", "late", "half_day"]
    notes: str | None = Field(default=None, max_length=500)


class AttendanceRead(ORMModel):
    id: int
    employee_id: int
    employee_name: str
    attendance_date: date
    status: str
    notes: str | None
    recorded_by_id: int
    created_at: datetime


class AttendanceSummary(ORMModel):
    present: int
    absent: int
    late: int
    half_day: int
    total: int

