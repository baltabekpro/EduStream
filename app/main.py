from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import os
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import Base, engine

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting EduStream API...")

    # During tests we use an isolated SQLite engine from tests/conftest.py.
    # Avoid touching the configured DB (often Postgres) on startup.
    is_pytest = (
        "PYTEST_CURRENT_TEST" in os.environ
        or os.environ.get("EDUSTREAM_TESTING") == "1"
        or "pytest" in sys.modules
    )
    if not is_pytest:
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("Skipping DB initialization on startup (testing mode)")
    logger.info(f"Documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EduStream API...")


# Create FastAPI app
app = FastAPI(
    title="EduStream API",
    description="Virtual Teaching Assistant API - Aligned with Swagger Specification",
    version="1.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Global exception handlers as per Swagger spec
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Global validation error handler.
    Returns standardized error response: {code, message, details}
    """
    errors = {}
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        errors[field] = error["msg"]
    
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "Validation Error",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    Returns standardized error response.
    """
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal Server Error",
            "details": {"error": str(exc)}
        }
    )


# Include API router
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to EduStream API",
        "docs": "/docs",
        "version": "1.4.0",
        "swagger_compliant": True
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
