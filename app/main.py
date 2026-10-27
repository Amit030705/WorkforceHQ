from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.core.config import get_settings
from app.services.errors import Conflict, InvalidOperation, RecordNotFound, ServiceError

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="PostgreSQL-backed employee management for administrators and employees.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(api_router)


@app.exception_handler(ServiceError)
def handle_service_error(request: Request, error: ServiceError):
    status_code = (
        404 if isinstance(error, RecordNotFound)
        else 409 if isinstance(error, Conflict)
        else 422 if isinstance(error, InvalidOperation)
        else 500
    )
    return JSONResponse(status_code=status_code, content={"detail": str(error)})


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/health", tags=["Health"])
def health():
    return JSONResponse({"status": "ok"})
