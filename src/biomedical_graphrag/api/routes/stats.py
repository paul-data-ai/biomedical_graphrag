"""Statistics routes for database metrics."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from biomedical_graphrag.api.models import StatsResponse
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import AsyncNeo4jClient
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/", response_model=StatsResponse)
async def get_database_stats() -> StatsResponse:
    """
    Get comprehensive database statistics.

    Returns counts of papers, genes, authors, institutions, and MeSH terms
    from the Neo4j knowledge graph.

    Returns:
        StatsResponse with database counts and last updated timestamp

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        settings = Settings()
        client = AsyncNeo4jClient(settings=settings)

        # Query for counts
        cypher_query = """
        MATCH (p:PAPER)
        WITH count(p) as paper_count
        MATCH (g:GENE)
        WITH paper_count, count(g) as gene_count
        MATCH (a:AUTHOR)
        WITH paper_count, gene_count, count(a) as author_count
        MATCH (i:INSTITUTION)
        WITH paper_count, gene_count, author_count, count(i) as institution_count
        MATCH (m:MESHTERM)
        RETURN
            paper_count,
            gene_count,
            author_count,
            institution_count,
            count(m) as meshterm_count
        """

        results = await client.query(cypher_query)

        if results:
            stats = results[0]
            return StatsResponse(
                total_papers=stats.get("paper_count", 0),
                total_genes=stats.get("gene_count", 0),
                total_authors=stats.get("author_count", 0),
                total_institutions=stats.get("institution_count", 0),
                total_mesh_terms=stats.get("meshterm_count", 0),
                last_updated=datetime.now()
            )
        else:
            # Return zeros if no data
            return StatsResponse(
                total_papers=0,
                total_genes=0,
                total_authors=0,
                total_institutions=0,
                total_mesh_terms=0,
                last_updated=datetime.now()
            )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database stats: {str(e)}"
        ) from e
