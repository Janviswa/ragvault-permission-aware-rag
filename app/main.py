import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.db import Base, engine
from app.config import settings
import app.models
from app.vectorstore.qdrant import get_client
from app.auth.routes import router as auth_router
from app.documents.routes import router as documents_router
from app.documents.permissions import router as permissions_router
from app.documents.access_requests import router as access_requests_router
from app.admin.access_requests import router as admin_access_requests_router
from app.admin.security import router as admin_security_router
from app.admin.audit import router as admin_audit_router
from app.admin.users import router as admin_users_router
from app.rag.routes import router as rag_router
from app.documents.upload import router as upload_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("ragvault")
Base.metadata.create_all(bind=engine)
app = FastAPI(title="RAGVault API", version="0.1.0")
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(permissions_router)
app.include_router(access_requests_router)
app.include_router(admin_access_requests_router)
app.include_router(admin_security_router)
app.include_router(admin_audit_router)
app.include_router(admin_users_router)
app.include_router(rag_router)
app.include_router(upload_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = [
        {
            "loc": error.get("loc", ()),
            "msg": error.get("msg", "Invalid request"),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

@app.get("/health")
def health():
    status = {"api": "ok"}
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:
        log.warning("postgres_unreachable %s", type(e).__name__)
        status["postgres"] = "error"
    try:
        get_client().get_collections()
        status["qdrant"] = "ok"
    except Exception as e:
        log.warning("qdrant_unreachable %s", type(e).__name__)
        status["qdrant"] = "error"
    return status
