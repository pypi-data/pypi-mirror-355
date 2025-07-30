"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database import init_database, close_database
from .routers import ai, audio, avatar, camera, robot, websocket, conversations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    print("🚀 Starting Tektra AI Assistant Backend...")
    try:
        await init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("✅ Backend started without database")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Tektra AI Assistant Backend...")
    try:
        await close_database()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"⚠️  Database cleanup failed: {e}")
    print("✅ Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Include routers
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio"])
app.include_router(avatar.router, prefix="/api/v1/avatar", tags=["Avatar"])
app.include_router(camera.router, prefix="/api/v1/camera", tags=["Camera"])
app.include_router(robot.router, prefix="/api/v1/robots", tags=["Robots"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/api")
async def root() -> JSONResponse:
    """Root endpoint with API information."""
    return JSONResponse({
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "status": "healthy",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    })


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "tektra-backend",
        "version": settings.api_version
    })


@app.get("/debug/frontend")
async def debug_frontend() -> JSONResponse:
    """Debug frontend path resolution."""
    try:
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "frontend" / "out",
            Path.cwd() / "frontend" / "out",
            Path(__file__).parent / "frontend" / "out",
        ]
        
        debug_info = {
            "current_working_directory": str(Path.cwd()),
            "main_file_location": str(Path(__file__)),
            "possible_frontend_paths": [
                {"path": str(p), "exists": p.exists(), "files": [str(f) for f in p.glob("*")] if p.exists() else []}
                for p in possible_paths
            ]
        }
        return JSONResponse(debug_info)
    except Exception as e:
        return JSONResponse({"error": str(e)})


# Mount static files for frontend (must be after API routes)
# Try multiple possible locations for frontend files
possible_frontend_paths = [
    Path(__file__).parent.parent.parent.parent / "frontend" / "out",  # Development
    Path.cwd() / "frontend" / "out",  # When run from project root
    Path(__file__).parent.parent / "frontend",  # Package structure
]

frontend_out_path = None
for path in possible_frontend_paths:
    if path.exists():
        frontend_out_path = path
        break

if frontend_out_path:
    print(f"✅ Mounting frontend from: {frontend_out_path}")
    # Mount Next.js static files
    next_static_path = frontend_out_path / "_next" / "static"
    if next_static_path.exists():
        app.mount("/_next/static", StaticFiles(directory=str(next_static_path)), name="nextstatic")
    
    # Mount main frontend (must be last)
    app.mount("/", StaticFiles(directory=str(frontend_out_path), html=True), name="frontend")
else:
    print("⚠️  Frontend files not found - running API only")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="debug" if settings.debug else "info",
    )