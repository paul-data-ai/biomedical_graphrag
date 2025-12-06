"""Request models for API endpoints."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for natural language queries."""

    question: str = Field(..., description="Natural language question", min_length=1, max_length=500)
    mode: str = Field(
        default="hybrid",
        description="Query mode: 'hybrid' (graph + vector), 'graph' (only graph), or 'vector' (only vector)",
    )
    limit: int = Field(default=10, description="Maximum number of results", ge=1, le=100)

    model_config = {"json_schema_extra": {"examples": [{"question": "What are the latest findings on CRISPR?", "mode": "hybrid", "limit": 10}]}}


class SearchRequest(BaseModel):
    """Request model for vector similarity search."""

    query: str = Field(..., description="Search query text", min_length=1, max_length=500)
    limit: int = Field(default=10, description="Number of results", ge=1, le=100)
    score_threshold: float = Field(default=0.7, description="Minimum similarity score", ge=0.0, le=1.0)

    model_config = {"json_schema_extra": {"examples": [{"query": "CRISPR gene editing", "limit": 10, "score_threshold": 0.7}]}}


class GraphExploreRequest(BaseModel):
    """Request model for graph exploration."""

    node_id: str = Field(..., description="Node identifier to explore")
    node_type: str = Field(..., description="Type of node: 'paper', 'author', 'gene', 'institution', or 'meshterm'")
    depth: int = Field(default=1, description="Exploration depth (number of hops)", ge=1, le=3)

    model_config = {"json_schema_extra": {"examples": [{"node_id": "PMID:12345678", "node_type": "paper", "depth": 1}]}}
