"""SmartMed FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import analytics, auth, caregivers, dose_history, medicines, schedules, verification
from app.config import get_settings
from app.database.session import init_db, session_scope
from app.ocr.pipeline import tesseract_available
from app.seed import seed_if_empty

logger = logging.getLogger("smartmed")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    init_db()
    with session_scope() as db:
        seed_if_empty(db)
    if not tesseract_available():
        logger.warning("Tesseract is not available. Photo verification will return a setup error until it is installed.")
    logger.info("SmartMed API listening. Environment=%s", settings.environment)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="SmartMed",
        description=(
            "Medication reminder and package-label verification assistant. "
            "SmartMed does not diagnose, prescribe, or confirm that a medicine is safe to take."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(auth.router)
    application.include_router(medicines.router)
    application.include_router(schedules.router)
    application.include_router(verification.router)
    application.include_router(dose_history.router)
    application.include_router(analytics.router)
    application.include_router(caregivers.router)

    @application.get("/health")
    def health():
        return {
            "status": "ok",
            "ocr_available": tesseract_available(),
            "smtp_configured": settings.smtp_configured,
            "version": settings.app_version,
        }

    @application.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @application.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        messages = []
        for error in exc.errors():
            location = " ".join(str(part) for part in error.get("loc", []) if part != "body")
            messages.append(f"{location}: {error.get('msg', 'Invalid value')}".strip(": "))
        detail = messages[0] if messages else "Invalid request."
        return JSONResponse(status_code=422, content={"detail": detail, "errors": messages})

    @application.exception_handler(SQLAlchemyError)
    async def database_handler(_request: Request, exc: SQLAlchemyError):
        logger.exception("Database error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "A database error occurred. Please try again."})

    @application.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})

    return application


app = create_app()
