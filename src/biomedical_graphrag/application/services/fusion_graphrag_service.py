"""Service for hybrid GraphRAG queries combining Qdrant and Neo4j."""

from biomedical_graphrag.application.services.hybrid_service.tool_calling import (
    run_graph_enrichment_and_summarize,
)
from biomedical_graphrag.application.services.query_vectorstore_service.qdrant_query import (
    AsyncQdrantQuery,
)
from biomedical_graphrag.config import Settings
from biomedical_graphrag.utils.logger_util import setup_logging

logger = setup_logging()


class FusionGraphRAGService:
    """Service for executing fusion GraphRAG queries."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the fusion service.

        Args:
            settings: Application settings (optional)
        """
        self.settings = settings or Settings()
        self._qdrant_query: AsyncQdrantQuery | None = None

    async def query(self, question: str, top_k: int = 10) -> dict:
        """
        Execute a hybrid fusion query combining vector search and graph enrichment.

        Args:
            question: Natural language question
            top_k: Number of documents to retrieve from Qdrant

        Returns:
            Dictionary with answer and supporting data
        """
        logger.info(f"Processing fusion query: {question}")

        # Initialize Qdrant query if needed
        if self._qdrant_query is None:
            self._qdrant_query = AsyncQdrantQuery()

        try:
            # Step 1: Retrieve semantic context from Qdrant
            documents = await self._qdrant_query.retrieve_documents(question, top_k=top_k)
            chunks = []
            for doc in documents:
                payload = doc.get("payload", {})
                if isinstance(payload, dict) and "content" in payload:
                    chunks.append(str(payload["content"]))
                else:
                    chunks.append(str(payload))

            # Step 2: Enrichment + Fusion summary
            answer = run_graph_enrichment_and_summarize(question, chunks)

            return {
                "answer": answer,
                "documents": documents,
                "source_chunks": len(chunks),
            }

        except Exception as e:
            logger.error(f"Error in fusion query: {e}")
            raise

    async def close(self):
        """Close the Qdrant connection."""
        if self._qdrant_query is not None:
            await self._qdrant_query.close()
            self._qdrant_query = None
