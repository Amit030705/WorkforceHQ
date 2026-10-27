from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, select

from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.common import Page
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.departments import create_department as create_department_service
from app.services.departments import delete_department as delete_department_service
from app.services.departments import update_department as update_department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


def department_select():
    return select(
        Department.id,
        Department.name,
        Department.description,
        func.count(Employee.id).label("employee_count"),
        Department.created_at,
        Department.updated_at,
    ).outerjoin(Employee).group_by(Department.id)


@router.get("", response_model=Page[DepartmentRead])
def list_departments(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
):
    total = db.scalar(select(func.count(Department.id))) or 0
    rows = db.execute(
        department_select().order_by(Department.name).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return Page(items=[DepartmentRead(**row._mapping) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, admin: AdminUser, db: DbSession):
    department = create_department_service(db, payload)
    row = db.execute(department_select().where(Department.id == department.id)).one()
    return DepartmentRead(**row._mapping)


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(department_id: int, payload: DepartmentUpdate, admin: AdminUser, db: DbSession):
    department = update_department_service(db, department_id, payload)
    row = db.execute(department_select().where(Department.id == department_id)).one()
    return DepartmentRead(**row._mapping)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, admin: AdminUser, db: DbSession):
    delete_department_service(db, department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
