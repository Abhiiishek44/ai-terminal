# app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from core.config import get_settings
from routers import terminal_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready AI Terminal Backend - Convert natural language to terminal commands using Gemini AI",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(terminal_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Terminal Backend API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "generate_command": "POST /terminal/run",
            "suggest_fix": "POST /terminal/fix",
            "health_check": "GET /terminal/health"
        }
    }


@app.get("/health", tags=["Root"])
async def health():
    """Global health check"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if settings.debug else "An error occurred",
            "status": "error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
