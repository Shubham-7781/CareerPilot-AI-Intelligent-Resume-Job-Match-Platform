import logging
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.services.rate_limiter import is_rate_limited
from app.api.routes import auth as auth_routes
from app.api.routes import resumes as resume_routes
from app.api.routes import jobs as job_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("careerpilot")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting: Redis-backed sliding window (falls back to in-memory
# per-process limiting automatically if Redis is unreachable — see
# app/services/rate_limiter.py). Redis-backed limiting is what makes this
# correct across multiple API replicas, unlike a purely in-memory counter. ---


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    if is_rate_limited(client_ip, settings.RATE_LIMIT_PER_MINUTE, window_seconds=60):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again shortly."},
        )

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health", tags=["system"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


app.include_router(auth_routes.router)
app.include_router(resume_routes.router)
app.include_router(job_routes.router)
