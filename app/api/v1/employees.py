from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select

from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.models.employee import Employee
from app.schemas.common import Page
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services.employees import create_employee as create_employee_service
from app.services.employees import delete_employee as delete_employee_service
from app.services.employees import employee_query, update_employee as update_employee_service

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/me", response_model=EmployeeRead)
def my_profile(user: CurrentUser, db: DbSession):
    if user.employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No employee profile is linked to this account.")
    return db.scalar(employee_query().where(Employee.id == user.employee.id))


@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=160),
    department_id: int | None = Query(default=None, gt=0),
    employment_status: str | None = Query(default=None, pattern="^(active|inactive|on_leave|terminated)$"),
):
    query = employee_query()
    count_query = select(func.count(Employee.id))
    if user.role != "admin":
        if user.employee is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No employee profile is linked to this account.")
        query = query.where(Employee.id == user.employee.id)
        count_query = count_query.where(Employee.id == user.employee.id)
    else:
        if search:
            term = f"%{search.strip()}%"
            condition = or_(Employee.name.ilike(term), Employee.email.ilike(term), Employee.employee_code.ilike(term))
            query = query.where(condition)
            count_query = count_query.where(condition)
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)
        if employment_status:
            query = query.where(Employee.employment_status == employment_status)
            count_query = count_query.where(Employee.employment_status == employment_status)
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(Employee.id).offset((page - 1) * page_size).limit(page_size)).all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, admin: AdminUser, db: DbSession):
    return create_employee_service(db, payload)


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, user: CurrentUser, db: DbSession):
    if user.role != "admin" and (user.employee is None or user.employee.id != employee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only view your own employee profile.")
    employee = db.scalar(employee_query().where(Employee.id == employee_id))
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found.")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, payload: EmployeeUpdate, admin: AdminUser, db: DbSession):
    return update_employee_service(db, employee_id, payload)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, admin: AdminUser, db: DbSession):
    delete_employee_service(db, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
