from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.errors import Conflict, RecordNotFound


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    department = Department(**payload.model_dump())
    db.add(department)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("Department name already exists.") from exc
    return department


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise RecordNotFound("Department not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("Department name already exists.") from exc
    return department


def delete_department(db: Session, department_id: int) -> None:
    department = db.get(Department, department_id)
    if department is None:
        raise RecordNotFound("Department not found.")
    employee_count = db.scalar(select(func.count(Employee.id)).where(Employee.department_id == department_id)) or 0
    if employee_count:
        raise Conflict("Reassign employees before deleting this department.")
    db.delete(department)
    db.commit()
