"""API routes for the BioMedical GraphRAG API."""

from .query import router as query_router
from .search import router as search_router
from .graph import router as graph_router
from .health import router as health_router
from .stats import router as stats_router

__all__ = ["query_router", "search_router", "graph_router", "health_router", "stats_router"]
