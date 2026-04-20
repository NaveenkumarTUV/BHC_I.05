from datetime import datetime, timezone
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import ALLOWED_ORIGINS, validate_runtime_config
from backend.app.routes.bhc_routes import router as bhc_router
from backend.app.routes.deq_routes import router as deq_router
from backend.app.services.bhc_admin_auth import get_current_user
from backend.app.services.bhc_config_db import ALLOWED_EMAIL_DOMAIN, DEFAULT_ADMIN_EMAIL, init_config_db
from backend.app.services.bhc_workflow_service import initialize_workflow_storage
from backend.app.utils.paths import DATA_DIR, EXPORTS_DIR, FRONTEND_DIR, ensure_dir


LOGGER = logging.getLogger("bhc.app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def _request_id_from(request: Request) -> str:
    return str(getattr(request.state, "request_id", "")) or request.headers.get("X-Request-ID", "") or str(uuid.uuid4())

def create_app() -> FastAPI:
    app = FastAPI(title="BHC Quotation System", version="I.05", description="TÜV Rheinland India — Building Health Check-Up Quotation Management")

    @app.on_event("startup")
    async def startup_init() -> None:
        validate_runtime_config()
        ensure_dir(DATA_DIR)
        ensure_dir(EXPORTS_DIR)
        ensure_dir(EXPORTS_DIR / "bhc")
        ensure_dir(EXPORTS_DIR / "deq")
        initialize_workflow_storage()
        init_config_db()
        LOGGER.info("Startup completed.")

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "").strip() or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    app.include_router(bhc_router)
    app.include_router(deq_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = _request_id_from(request)
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": request_id},
            content={
                "detail": detail,
                "error_code": f"HTTP_{exc.status_code}",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = _request_id_from(request)
        LOGGER.exception("Unhandled exception request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            headers={"X-Request-ID": request_id},
            content={
                "detail": "Unexpected server error. Contact support with request_id.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.get("/")
    async def root_redirect():
        return RedirectResponse(url="/bhc", status_code=307)

    @app.get("/api/health")
    async def api_health():
        return {
            "status": "ok",
            "service": "bhc-quotation-system",
            "version": "I.05",
            "build": "enterprise",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/api/session")
    async def api_session(request: Request):
        user = get_current_user(request)
        return {
            "authenticated": bool(user),
            "email": user.get("email", "") if user else "",
            "full_name": user.get("full_name", "") if user else "",
            "username": user.get("full_name", "") if user else "Guest",
            "is_admin": bool(user.get("is_admin")) if user else False,
            "must_change_password": bool(user.get("must_change_password")) if user else False,
            "designation": user.get("designation", "") if user else "",
            "has_signature": bool(user.get("has_signature")) if user else False,
            "has_security_question": bool(user.get("has_security_question")) if user else False,
            "allowed_domain": ALLOWED_EMAIL_DOMAIN,
            "admin_email": DEFAULT_ADMIN_EMAIL,
        }

    @app.get("/api/assets/tuv-logo")
    async def api_tuv_logo():
        logo_path = DATA_DIR / "tuv_logo.png"
        if not logo_path.exists():
            raise HTTPException(status_code=404, detail="Logo file not found")
        return FileResponse(str(logo_path), media_type="image/png")

    app.mount("/bhc", StaticFiles(directory=str(FRONTEND_DIR / "bhc"), html=True), name="bhc-frontend")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=7860,
        log_level="info",
    )
