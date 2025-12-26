"""
MiniCloud Platform - Control Plane API
AWS-like self-hosted cloud platform

Architecture following SOLID Principles:
- S: Single Responsibility - Each module has one job
- O: Open/Closed - Easy to extend without modifying
- L: Liskov Substitution - Services/Repos are substitutable
- I: Interface Segregation - Small, focused interfaces
- D: Dependency Inversion - Depend on abstractions

Project Structure:
├── config.py       - Configuration and settings
├── database.py     - Database and MinIO connections
├── models.py       - Pydantic request/response models
├── repositories.py - Data access layer (DAO)
├── services.py     - Business logic layer
├── routers.py      - HTTP endpoints (controllers)
└── main.py         - Application entry point (this file)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import app_config
from .database import db, storage
from .routers import all_routers


def create_app() -> FastAPI:
    """Application factory - creates and configures the FastAPI app"""
    
    app = FastAPI(
        title=app_config.title,
        description=app_config.description,
        version=app_config.version,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register all routers
    for router in all_routers:
        app.include_router(router)
    
    # Lifecycle events
    @app.on_event("startup")
    async def startup():
        """Initialize connections on startup"""
        await db.connect()
        storage.connect()
        print("🚀 MiniCloud API started")
    
    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown"""
        await db.disconnect()
        print("👋 MiniCloud API stopped")
    
    return app


# Create the application instance
app = create_app()


# Development entrypoint
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
