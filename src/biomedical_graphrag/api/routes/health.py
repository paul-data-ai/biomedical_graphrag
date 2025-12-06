"""Health check routes for system monitoring."""

import time
from datetime import datetime
from fastapi import APIRouter
from loguru import logger

from biomedical_graphrag.api.models import SystemHealth
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import AsyncNeo4jClient
from biomedical_graphrag.infrastructure.qdrant_db.qdrant_vectorstore import QdrantVectorStore
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/health", tags=["health"])

# Track app start time for uptime calculation
_start_time = time.time()


@router.get("/", response_model=SystemHealth)
async def get_health_status() -> SystemHealth:
    """
    Get comprehensive system health status.

    Checks connectivity to Neo4j, Qdrant, and Prefect services.

    Returns:
        SystemHealth with status of all components
    """
    neo4j_connected = False
    qdrant_connected = False
    prefect_running = False

    # Check Neo4j
    try:
        settings = Settings()
        neo4j_client = AsyncNeo4jClient(settings=settings)
        await neo4j_client.query("RETURN 1")
        neo4j_connected = True
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")

    # Check Qdrant
    try:
        vectorstore = QdrantVectorStore(settings=settings)
        # Try to get collection info
        qdrant_connected = await vectorstore.check_connection()
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")

    # Check Prefect (simplified - just check if we can import)
    try:
        import prefect  # noqa: F401
        prefect_running = True
    except Exception:
        prefect_running = False

    # Determine overall status
    if neo4j_connected and qdrant_connected:
        status = "healthy"
    elif neo4j_connected or qdrant_connected:
        status = "degraded"
    else:
        status = "down"

    # Calculate uptime
    uptime_seconds = time.time() - _start_time

    return SystemHealth(
        status=status,
        neo4j_connected=neo4j_connected,
        qdrant_connected=qdrant_connected,
        api_online=True,  # If we're responding, API is online
        prefect_running=prefect_running,
        rate_limit_percent=0.0,  # TODO: Implement rate limit tracking
        last_update=datetime.now(),
        uptime_seconds=uptime_seconds
    )
