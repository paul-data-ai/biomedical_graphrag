"""Search routes for vector similarity search."""

import time
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from biomedical_graphrag.api.models import SearchRequest, SearchResponse, PaperResult
from biomedical_graphrag.infrastructure.qdrant_db.qdrant_vectorstore import QdrantVectorStore
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/search", tags=["search"])

# Global vectorstore instance
_vectorstore: QdrantVectorStore | None = None


async def get_vectorstore() -> QdrantVectorStore:
    """Get or create the vectorstore instance."""
    global _vectorstore
    if _vectorstore is None:
        settings = Settings()
        _vectorstore = QdrantVectorStore(settings=settings)
    return _vectorstore


@router.post("/", response_model=SearchResponse)
async def vector_search(request: SearchRequest) -> SearchResponse:
    """
    Execute vector similarity search across biomedical papers.

    Uses Qdrant vector database to find semantically similar papers
    based on the search query.

    Args:
        request: Search request with query text, limit, and score threshold

    Returns:
        SearchResponse with matching papers and metadata

    Raises:
        HTTPException: If search execution fails
    """
    start_time = time.time()

    try:
        logger.info(f"Vector search: {request.query}")

        vectorstore = await get_vectorstore()

        # Perform similarity search
        results = await vectorstore.similarity_search(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold
        )

        # Convert to PaperResult format
        papers = []
        for result in results:
            papers.append(PaperResult(
                pmid=result.get("pmid", ""),
                title=result.get("title", ""),
                abstract=result.get("abstract"),
                publication_date=result.get("publication_date"),
                authors=result.get("authors", []),
                genes=result.get("genes", []),
                mesh_terms=result.get("mesh_terms", []),
                score=result.get("score")
            ))

        execution_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=papers,
            total_count=len(papers),
            execution_time_ms=execution_time_ms
        )

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search execution failed: {str(e)}"
        ) from e
