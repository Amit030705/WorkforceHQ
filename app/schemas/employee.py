from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import EmailStr, Field, StringConstraints, field_validator
from typing_extensions import Annotated

from app.schemas.common import ORMModel

EmploymentStatus = Literal["active", "inactive", "on_leave", "terminated"]


class EmployeeCreate(ORMModel):
    employee_code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    department_id: int = Field(gt=0)
    designation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    joining_date: date
    salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    employment_status: EmploymentStatus = "active"
    password: str = Field(min_length=12, max_length=128, exclude=True)


class EmployeeUpdate(ORMModel):
    employee_code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)] | None = None
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)] | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    department_id: int | None = Field(default=None, gt=0)
    designation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)] | None = None
    joining_date: date | None = None
    salary: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    employment_status: EmploymentStatus | None = None

    @field_validator(
        "employee_code", "name", "email", "department_id", "designation",
        "joining_date", "salary", "employment_status",
    )
    @classmethod
    def reject_null_updates(cls, value):
        if value is None:
            raise ValueError("Provide a value or leave the field out; null is not a valid update.")
        return value


class EmployeeRead(ORMModel):
    id: int
    employee_code: str
    name: str
    email: EmailStr
    phone: str | None
    department_id: int
    department_name: str
    designation: str
    joining_date: date
    salary: Decimal
    employment_status: str
    user_id: int
    created_at: datetime
    updated_at: datetime
