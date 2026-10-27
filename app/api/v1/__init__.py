from fastapi import APIRouter

from app.api.v1.attendance import router as attendance_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.departments import router as departments_router
from app.api.v1.employees import router as employees_router
from app.api.v1.leaves import router as leaves_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(employees_router)
router.include_router(departments_router)
router.include_router(attendance_router)
router.include_router(leaves_router)
router.include_router(dashboard_router)

