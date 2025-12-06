"""Response models for API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaperResult(BaseModel):
    """Paper search result."""

    pmid: str
    title: str
    abstract: str | None = None
    publication_date: str | None = None
    authors: list[str] = Field(default_factory=list)
    genes: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)
    score: float | None = None


class AuthorResult(BaseModel):
    """Author result."""

    name: str
    paper_count: int = 0
    collaborators: list[str] = Field(default_factory=list)


class GeneResult(BaseModel):
    """Gene result."""

    gene_id: str
    symbol: str
    description: str | None = None
    paper_count: int = 0


class QueryResponse(BaseModel):
    """Response for natural language queries."""

    question: str
    answer: str
    papers: list[PaperResult] = Field(default_factory=list)
    authors: list[AuthorResult] = Field(default_factory=list)
    genes: list[GeneResult] = Field(default_factory=list)
    graph_data: dict[str, Any] | None = None
    execution_time_ms: float
    query_type: str

    model_config = {"json_schema_extra": {"examples": [
        {
            "question": "What are the latest findings on CRISPR?",
            "answer": "Recent research shows...",
            "papers": [],
            "authors": [],
            "genes": [],
            "execution_time_ms": 234.5,
            "query_type": "hybrid"
        }
    ]}}


class SearchResponse(BaseModel):
    """Response for vector similarity search."""

    query: str
    results: list[PaperResult]
    total_count: int
    execution_time_ms: float


class GraphNode(BaseModel):
    """Graph node data."""

    id: str
    type: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Graph edge data."""

    source: str
    target: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """Graph visualization data."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    center_node: str
    execution_time_ms: float


class SystemHealth(BaseModel):
    """System health status."""

    status: str = Field(description="Overall system status: 'healthy', 'degraded', or 'down'")
    neo4j_connected: bool
    qdrant_connected: bool
    api_online: bool
    prefect_running: bool
    rate_limit_percent: float = Field(description="Current rate limit usage percentage", ge=0.0, le=100.0)
    last_update: datetime
    uptime_seconds: float


class StatsResponse(BaseModel):
    """Database statistics."""

    total_papers: int
    total_genes: int
    total_authors: int
    total_institutions: int
    total_mesh_terms: int
    last_updated: datetime | None = None
