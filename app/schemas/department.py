from datetime import datetime

from pydantic import Field, StringConstraints
from typing_extensions import Annotated

from app.schemas.common import ORMModel


class DepartmentCreate(ORMModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    description: str | None = Field(default=None, max_length=500)


class DepartmentUpdate(ORMModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)] | None = None
    description: str | None = Field(default=None, max_length=500)


class DepartmentRead(ORMModel):
    id: int
    name: str
    description: str | None
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime

