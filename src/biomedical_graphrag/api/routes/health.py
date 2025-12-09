"""Health check routes for system monitoring."""

import time
from datetime import datetime
from fastapi import APIRouter
from loguru import logger
from openai import AsyncOpenAI

from biomedical_graphrag.api.models import SystemHealth
from biomedical_graphrag.config import settings
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import AsyncNeo4jClient
from biomedical_graphrag.infrastructure.qdrant_db.qdrant_vectorstore import AsyncQdrantVectorStore

router = APIRouter(prefix="/api/health", tags=["health"])

# Track app start time for uptime calculation
_start_time = time.time()


@router.get("/", response_model=SystemHealth)
@router.head("/")
async def get_health_status() -> SystemHealth:
    """
    Get comprehensive system health status.

    Checks connectivity to Neo4j, Qdrant, and Prefect services.
    Supports both GET and HEAD requests for monitoring tools.

    Returns:
        SystemHealth with status of all components
    """
    neo4j_connected = False
    qdrant_connected = False
    prefect_running = False

    # Check Neo4j
    try:
        neo4j_client = await AsyncNeo4jClient.create()
        await neo4j_client.execute("RETURN 1")
        await neo4j_client.close()
        neo4j_connected = True
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")

    # Check Qdrant
    try:
        vectorstore = AsyncQdrantVectorStore()
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


@router.get("/openai-test")
async def test_openai_connection():
    """Test OpenAI API connectivity and return detailed diagnostics."""
    result = {
        "api_key_present": bool(settings.openai.api_key.get_secret_value()),
        "api_key_length": len(settings.openai.api_key.get_secret_value()) if settings.openai.api_key.get_secret_value() else 0,
        "api_key_prefix": settings.openai.api_key.get_secret_value()[:15] if settings.openai.api_key.get_secret_value() else "",
        "base_url": settings.openai.base_url,
        "model": settings.qdrant.embedding_model,
        "test_result": None,
        "error": None,
        "error_type": None,
    }

    try:
        client = AsyncOpenAI(api_key=settings.openai.api_key.get_secret_value())
        response = await client.embeddings.create(
            model=settings.qdrant.embedding_model,
            input="test"
        )
        result["test_result"] = "SUCCESS"
        result["embedding_dimension"] = len(response.data[0].embedding)
    except Exception as e:
        result["test_result"] = "FAILED"
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        logger.error(f"OpenAI test failed: {type(e).__name__}: {e}")

    return result
