"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, batch, data, discovery
from app.models.schemas import HealthResponse
from app.services.tilde_client import tilde_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    yield
    # Shutdown
    await tilde_client.close()


app = FastAPI(
    title="GeoNet Geomag API",
    description="REST API for accessing GeoNet's Tilde v4 geomagnetic data",
    version="1.0.0",
    lifespan=lifespan,
)

# Add response compression for large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS support for web container
web_origin = os.getenv("WEB_ORIGIN", "*")
allow_origins = [web_origin] if web_origin != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(discovery.router)
app.include_router(data.router)
app.include_router(analytics.router)
app.include_router(batch.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="geomag-api")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "GeoNet Geomag API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
