"""Main FastAPI application for BioMedical GraphRAG API."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger

from biomedical_graphrag.api.routes import (
    query_router,
    search_router,
    graph_router,
    health_router,
    stats_router,
    sessions_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting BioMedical GraphRAG API...")
    logger.info("API is ready to accept requests")
    yield
    # Shutdown
    logger.info("Shutting down BioMedical GraphRAG API...")


# Create FastAPI application
app = FastAPI(
    title="BioMedical GraphRAG API",
    description=(
        "Production-ready API for biomedical research using GraphRAG technology. "
        "Combines Neo4j knowledge graphs with Qdrant vector search for "
        "intelligent querying of biomedical literature and genomic data."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:5173",  # Vite dev server (alternative)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://frontend-pi-drab-99.vercel.app",  # Vercel production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(query_router)
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(health_router)
app.include_router(stats_router)
app.include_router(sessions_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api")
async def api_info():
    """
    Get API information and available endpoints.

    Returns:
        Dict with API metadata
    """
    return {
        "name": "BioMedical GraphRAG API",
        "version": "1.0.0",
        "description": "Natural language querying for biomedical research",
        "endpoints": {
            "query": "/api/query - Natural language GraphRAG queries",
            "search": "/api/search - Vector similarity search",
            "graph": "/api/graph/explore - Graph exploration",
            "health": "/api/health - System health status",
            "stats": "/api/stats - Database statistics",
            "sessions": "/api/sessions - Conversation session management",
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "biomedical_graphrag.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
