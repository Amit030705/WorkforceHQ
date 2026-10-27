from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.errors import Conflict, RecordNotFound


def employee_query():
    return select(Employee).options(joinedload(Employee.department))


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    if db.get(Department, payload.department_id) is None:
        raise RecordNotFound("Department not found.")
    email = str(payload.email).lower()
    user = User(email=email, password_hash=hash_password(payload.password), role="employee")
    employee_data = payload.model_dump(exclude={"password"})
    employee_data["email"] = email
    employee = Employee(user=user, **employee_data)
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("Employee code or email already exists.") from exc
    return db.scalar(employee_query().where(Employee.id == employee.id))


def update_employee(db: Session, employee_id: int, payload: EmployeeUpdate) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise RecordNotFound("Employee not found.")
    updates = payload.model_dump(exclude_unset=True)
    if "department_id" in updates and db.get(Department, updates["department_id"]) is None:
        raise RecordNotFound("Department not found.")
    if "email" in updates:
        updates["email"] = str(updates["email"]).lower()
        employee.user.email = updates["email"]
    for field, value in updates.items():
        setattr(employee, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("Employee code or email already exists.") from exc
    return db.scalar(employee_query().where(Employee.id == employee_id))


def delete_employee(db: Session, employee_id: int) -> None:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise RecordNotFound("Employee not found.")
    employee_user = employee.user
    db.delete(employee)
    db.flush()
    db.delete(employee_user)
    db.commit()

