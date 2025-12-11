"""Query routes for natural language GraphRAG queries."""

import json
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from biomedical_graphrag.api.models import QueryRequest, QueryResponse, PaperResult
from biomedical_graphrag.application.services.fusion_graphrag_service import FusionGraphRAGService
from biomedical_graphrag.application.services.conversation_memory_service import ConversationMemoryService
from biomedical_graphrag.config import Settings

router = APIRouter(prefix="/api/query", tags=["query"])

# Global service instances (will be initialized on startup)
_fusion_service: FusionGraphRAGService | None = None
_memory_service: ConversationMemoryService | None = None


async def get_fusion_service() -> FusionGraphRAGService:
    """Get or create the fusion service instance."""
    global _fusion_service
    if _fusion_service is None:
        settings = Settings()
        _fusion_service = FusionGraphRAGService(settings=settings)
    return _fusion_service


def get_memory_service() -> ConversationMemoryService:
    """Get or create the conversation memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = ConversationMemoryService(max_messages=10)
    return _memory_service


@router.post("/", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_graphrag(request: QueryRequest) -> QueryResponse:
    """
    Execute a natural language query using GraphRAG with conversation memory.

    This endpoint combines graph database queries (Neo4j) with vector similarity search (Qdrant)
    to provide comprehensive answers to biomedical research questions. It maintains conversation
    context across multiple queries in the same session.

    Args:
        request: Query request with question, session_id (optional), mode, and limit

    Returns:
        QueryResponse with answer, session_id, papers, authors, genes, and graph data

    Raises:
        HTTPException: If query execution fails
    """
    start_time = time.time()

    try:
        logger.info(f"Processing query: {request.question}")

        # Get services
        fusion_service = await get_fusion_service()
        memory_service = get_memory_service()

        # Get or create session
        session_id = memory_service.create_session(request.session_id)
        logger.info(f"Using session: {session_id}")

        # Get conversation context from memory
        conversation_context = memory_service.get_conversation_context(session_id)

        # Prepare the question with context
        if conversation_context:
            contextualized_question = f"{conversation_context}\n\nCurrent question: {request.question}"
            logger.debug(f"Added conversation context to question")
        else:
            contextualized_question = request.question

        # Execute query based on mode
        if request.mode == "hybrid":
            result = await fusion_service.query(question=contextualized_question, top_k=request.limit)
        elif request.mode == "graph":
            result = await fusion_service.query_graph_only(question=contextualized_question, top_k=request.limit)
        elif request.mode == "vector":
            result = await fusion_service.query_vector_only(question=contextualized_question, top_k=request.limit)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.mode}. Use 'hybrid', 'graph', or 'vector'."
            )

        answer = result.get("answer", "No answer generated")

        # Add this exchange to conversation memory
        memory_service.add_message(
            session_id=session_id,
            human_message=request.question,  # Store original question, not contextualized
            ai_message=answer
        )
        logger.info(f"Added conversation to session {session_id}")

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
            answer=answer,
            session_id=session_id,
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


@router.post("/stream")
async def query_graphrag_stream(request: QueryRequest):
    """
    Stream a natural language query response using GraphRAG with conversation memory.

    Returns results as Server-Sent Events for real-time streaming.
    """
    async def generate():
        """Generate streaming response."""
        start_time = time.time()

        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'content': 'Processing query...'})}\n\n"

            # Get services
            fusion_service = await get_fusion_service()
            memory_service = get_memory_service()

            # Get or create session
            session_id = memory_service.create_session(request.session_id)
            logger.info(f"Using session: {session_id}")

            # Send session ID to frontend
            yield f"data: {json.dumps({'type': 'session', 'content': session_id})}\n\n"

            # Get conversation context from memory
            conversation_context = memory_service.get_conversation_context(session_id)

            # Prepare the question with context
            if conversation_context:
                contextualized_question = f"{conversation_context}\n\nCurrent question: {request.question}"
                logger.debug(f"Added conversation context to question")
            else:
                contextualized_question = request.question

            # Execute query
            yield f"data: {json.dumps({'type': 'status', 'content': 'Searching databases...'})}\n\n"

            result = await fusion_service.query(question=contextualized_question, top_k=request.limit)

            # Stream the answer
            answer = result.get("answer", "No answer generated")
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating answer...'})}\n\n"

            # Stream answer in chunks (simulate streaming - in real implementation, this would come from LLM streaming)
            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'answer_chunk', 'content': chunk})}\n\n"

            # Add this exchange to conversation memory
            memory_service.add_message(
                session_id=session_id,
                human_message=request.question,  # Store original question, not contextualized
                ai_message=answer
            )
            logger.info(f"Added conversation to session {session_id}")

            # Send papers data
            papers = []
            if result.get("papers"):
                for paper in result["papers"][:request.limit]:
                    papers.append({
                        "pmid": paper.get("pmid", ""),
                        "title": paper.get("title", ""),
                        "abstract": paper.get("abstract"),
                        "publication_date": paper.get("publication_date"),
                        "authors": paper.get("authors", []),
                        "genes": paper.get("genes", []),
                        "mesh_terms": paper.get("mesh_terms", []),
                        "score": paper.get("score")
                    })

            execution_time_ms = (time.time() - start_time) * 1000

            # Send final data
            yield f"data: {json.dumps({'type': 'papers', 'content': papers})}\n\n"
            yield f"data: {json.dumps({'type': 'metadata', 'content': {'execution_time_ms': execution_time_ms, 'query_type': request.mode, 'session_id': session_id}})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


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
