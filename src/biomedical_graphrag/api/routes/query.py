"""Query routes for natural language GraphRAG queries."""

import time
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from biomedical_graphrag.api.models import QueryRequest, QueryResponse, PaperResult
from biomedical_graphrag.application.services.fusion_graphrag_service import FusionGraphRAGService
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/query", tags=["query"])

# Global service instance (will be initialized on startup)
_fusion_service: FusionGraphRAGService | None = None


async def get_fusion_service() -> FusionGraphRAGService:
    """Get or create the fusion service instance."""
    global _fusion_service
    if _fusion_service is None:
        settings = Settings()
        _fusion_service = FusionGraphRAGService(settings=settings)
    return _fusion_service


@router.post("/", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_graphrag(request: QueryRequest) -> QueryResponse:
    """
    Execute a natural language query using GraphRAG.

    This endpoint combines graph database queries (Neo4j) with vector similarity search (Qdrant)
    to provide comprehensive answers to biomedical research questions.

    Args:
        request: Query request with question, mode, and limit

    Returns:
        QueryResponse with answer, papers, authors, genes, and graph data

    Raises:
        HTTPException: If query execution fails
    """
    start_time = time.time()

    try:
        logger.info(f"Processing query: {request.question}")

        # Get fusion service
        fusion_service = await get_fusion_service()

        # Execute query based on mode
        if request.mode == "hybrid":
            result = await fusion_service.query(question=request.question, top_k=request.limit)
        elif request.mode == "graph":
            result = await fusion_service.query_graph_only(question=request.question, top_k=request.limit)
        elif request.mode == "vector":
            result = await fusion_service.query_vector_only(question=request.question, top_k=request.limit)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.mode}. Use 'hybrid', 'graph', or 'vector'."
            )

        # Parse results into structured response
        papers = []
        if result.get("papers"):
            for paper in result["papers"][:request.limit]:
                papers.append(PaperResult(
                    pmid=paper.get("pmid", ""),
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract"),
                    publication_date=paper.get("publication_date"),
                    authors=paper.get("authors", []),
                    genes=paper.get("genes", []),
                    mesh_terms=paper.get("mesh_terms", []),
                    score=paper.get("score")
                ))

        execution_time_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            question=request.question,
            answer=result.get("answer", "No answer generated"),
            papers=papers,
            authors=result.get("authors", []),
            genes=result.get("genes", []),
            graph_data=result.get("graph_data"),
            execution_time_ms=execution_time_ms,
            query_type=request.mode
        )

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        ) from e


@router.get("/examples", response_model=list[str])
async def get_example_queries() -> list[str]:
    """
    Get list of example queries for demo mode.

    Returns:
        List of example questions users can try
    """
    return [
        "What are the latest findings on CRISPR gene editing?",
        "Who collaborates with Jennifer Doudna on gene editing research?",
        "Which genes are mentioned in cancer immunotherapy papers?",
        "Show me papers about TP53 gene mutations",
        "What are the recent breakthroughs in Alzheimer's disease research?",
        "Which institutions lead in synthetic biology research?",
    ]
