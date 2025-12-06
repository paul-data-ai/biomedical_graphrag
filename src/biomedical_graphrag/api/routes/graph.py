"""Graph routes for Neo4j graph exploration."""

import time
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from biomedical_graphrag.api.models import GraphExploreRequest, GraphData, GraphNode, GraphEdge
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import AsyncNeo4jClient
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Global Neo4j client instance
_neo4j_client: AsyncNeo4jClient | None = None


async def get_neo4j_client() -> AsyncNeo4jClient:
    """Get or create the Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        settings = Settings()
        _neo4j_client = AsyncNeo4jClient(settings=settings)
    return _neo4j_client


@router.post("/explore", response_model=GraphData)
async def explore_graph(request: GraphExploreRequest) -> GraphData:
    """
    Explore the knowledge graph starting from a specific node.

    Retrieves connected nodes and relationships up to the specified depth.

    Args:
        request: Graph explore request with node_id, node_type, and depth

    Returns:
        GraphData with nodes and edges for visualization

    Raises:
        HTTPException: If graph exploration fails
    """
    start_time = time.time()

    try:
        logger.info(f"Exploring graph from {request.node_type} node: {request.node_id}")

        client = await get_neo4j_client()

        # Build Cypher query based on node type
        cypher_query = f"""
        MATCH (center:{request.node_type.upper()} {{id: $node_id}})
        CALL apoc.path.subgraphAll(center, {{
            maxLevel: $depth,
            relationshipFilter: null
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        results = await client.query(
            cypher_query,
            {"node_id": request.node_id, "depth": request.depth}
        )

        # Parse results into nodes and edges
        nodes = []
        edges = []

        if results:
            result = results[0]
            neo4j_nodes = result.get("nodes", [])
            neo4j_relationships = result.get("relationships", [])

            # Convert Neo4j nodes to GraphNode
            for node in neo4j_nodes:
                nodes.append(GraphNode(
                    id=node.get("id", str(node.element_id)),
                    type=list(node.labels)[0].lower() if node.labels else "unknown",
                    label=node.get("name") or node.get("title") or node.get("symbol") or node.get("id", "Unknown"),
                    properties=dict(node)
                ))

            # Convert Neo4j relationships to GraphEdge
            for rel in neo4j_relationships:
                edges.append(GraphEdge(
                    source=rel.start_node.get("id", str(rel.start_node.element_id)),
                    target=rel.end_node.get("id", str(rel.end_node.element_id)),
                    type=rel.type,
                    properties=dict(rel)
                ))

        execution_time_ms = (time.time() - start_time) * 1000

        return GraphData(
            nodes=nodes,
            edges=edges,
            center_node=request.node_id,
            execution_time_ms=execution_time_ms
        )

    except Exception as e:
        logger.error(f"Graph exploration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph exploration failed: {str(e)}"
        ) from e
