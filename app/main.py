from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager # For lifespan events in newer FastAPI

from app.core.config import settings
from app.api.v1.api_router_v1 import api_router_v1 # Your main v1 API router
from app.services_external.redis_client import RedisClient
# from app.database.session import create_db_and_tables # Optional: for initial setup during development


# Lifespan manager for startup and shutdown events (FastAPI 0.90.0+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print(f"Starting up {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    # Attempt to initialize Redis client on startup (optional, but good for early failure detection)
    try:
        await RedisClient.get_client_instance() # This will initialize if not already
    except ConnectionError as e:
        print(f"LIFESPAN STARTUP: Failed to connect to Redis during startup: {e}. Caching will be unavailable.")
    # ... other startup logic ...
    print("Application startup complete.")
    yield
    # --- Shutdown ---
    print(f"Shutting down {settings.PROJECT_NAME}...")
    await RedisClient.close_global_client() # Properly close the Redis connection
    # ... other shutdown logic ...
    print("Application shutdown complete.")

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # Customize OpenAPI schema URL
    docs_url=f"{settings.API_V1_STR}/docs",             # Customize Swagger UI URL
    redoc_url=f"{settings.API_V1_STR}/redoc",           # Customize ReDoc URL
    lifespan=lifespan # Use the lifespan context manager
)

# --- CORS (Cross-Origin Resource Sharing) ---
# Configure CORS to allow requests from your frontend application.
# SSR Section 8.5: General API Considerations (CORS)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS], # Origins allowed
        allow_credentials=True,
        allow_methods=["*"],    # Allow all methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],    # Allow all headers
    )
else:
    # If no origins are specified, you might want a restrictive default or log a warning.
    # For development, allowing "*" might be okay, but be specific for production.
    print("Warning: BACKEND_CORS_ORIGINS not set. CORS will be restrictive or default to browser same-origin policy.")
    # Example for local development if no .env setting:
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Common React dev port
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )


# --- Include API Routers ---
# Mount the v1 API router under the /api/v1 prefix
app.include_router(api_router_v1, prefix=settings.API_V1_STR)


# --- Global Exception Handlers (Optional) ---
# Example: Custom handler for Pydantic validation errors to provide a cleaner response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # You can customize the error response format here
    # For example, extract more details from exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Validation Error"},
    )

# Example: Custom handler for general HTTPExceptions (though FastAPI handles them well by default)
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"message": exc.detail, "custom_code": "YOUR_ERROR_CODE_IF_ANY"},
#     )


# --- Root Endpoint (Optional) ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic application information.
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "ssr_document_date": settings.SSR_DOCUMENT_DATE,
        "documentation_swagger": app.docs_url,
        "documentation_redoc": app.redoc_url
    }

# --- Running the app (for development with uvicorn directly) ---
# This part is typically not in main.py if you use a process manager like Gunicorn with Uvicorn workers
# or run `uvicorn app.main:app --reload` from the command line.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0", # Listen on all available IPs
#         port=8000,      # Standard port for FastAPI dev
#         reload=settings.DEBUG, # Enable auto-reload if DEBUG is True
#         log_level="info" if settings.DEBUG else "warning"
#     )
