from datetime import date, datetime
from typing import Literal

from pydantic import Field, StringConstraints
from typing_extensions import Annotated

from app.schemas.common import ORMModel


class LeaveCreate(ORMModel):
    start_date: date
    end_date: date
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]


class LeaveReview(ORMModel):
    status: Literal["approved", "rejected"]
    reviewer_comment: str | None = Field(default=None, max_length=500)


class LeaveRead(ORMModel):
    id: int
    employee_id: int
    employee_name: str
    start_date: date
    end_date: date
    reason: str
    status: str
    reviewed_at: datetime | None
    reviewer_id: int | None
    reviewer_email: str | None
    reviewer_comment: str | None
    created_at: datetime
    updated_at: datetime

