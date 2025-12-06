"""Prefect tasks for biomedical GraphRAG pipeline."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from prefect import get_run_logger, task
from prefect.artifacts import create_markdown_artifact

from biomedical_graphrag.config import settings
from biomedical_graphrag.data_sources.gene.gene_data_collector import GeneDataCollector
from biomedical_graphrag.data_sources.pubmed.pubmed_data_collector import (
    PubMedDataCollector,
)
from biomedical_graphrag.domain.dataset import GeneDataset, PaperDataset
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_client import AsyncNeo4jClient
from biomedical_graphrag.infrastructure.neo4j_db.neo4j_graph_schema import (
    Neo4jGraphIngestion,
)
from biomedical_graphrag.infrastructure.qdrant_db.qdrant_vectorstore import (
    AsyncQdrantVectorStore,
)
from biomedical_graphrag.orchestration.rate_limiter import (
    AdaptiveRateLimiter,
    RateLimitConfig,
)
from biomedical_graphrag.utils.json_util import load_gene_json, load_pubmed_json


# ==================== CONFIGURATION ====================
@task(
    name="validate_configuration",
    description="Validate all required configuration and API keys",
    retries=0,
    tags=["setup", "validation"],
)
async def validate_configuration() -> dict[str, Any]:
    """Validate configuration before starting pipeline."""
    logger = get_run_logger()
    logger.info("Validating configuration...")

    validation_results = {
        "openai_configured": bool(settings.openai.api_key),
        "neo4j_configured": bool(settings.neo4j.uri),
        "qdrant_configured": bool(settings.qdrant.url),
        "pubmed_email_configured": bool(settings.pubmed.email),
        "data_paths_valid": (
            Path(settings.json_data.pubmed_json_path).parent.exists()
            and Path(settings.json_data.gene_json_path).parent.exists()
        ),
    }

    all_valid = all(validation_results.values())

    if all_valid:
        logger.info("✅ All configuration validated successfully")
    else:
        failed = [k for k, v in validation_results.items() if not v]
        logger.error(f"❌ Configuration validation failed: {failed}")
        raise ValueError(f"Configuration validation failed: {failed}")

    return validation_results


# ==================== DATA COLLECTION ====================
@task(
    name="collect_pubmed_data",
    description="Collect PubMed papers with rate limiting",
    retries=3,
    retry_delay_seconds=300,  # 5 minute delay between retries
    timeout_seconds=3600,  # 1 hour timeout
    tags=["data_collection", "pubmed"],
)
async def collect_pubmed_data(
    search_terms: list[str] | None = None, max_results: int = 100
) -> dict[str, Any]:
    """
    Collect PubMed data with adaptive rate limiting.

    Args:
        search_terms: List of search terms (default uses config)
        max_results: Maximum results per search term

    Returns:
        Statistics about collected data
    """
    logger = get_run_logger()
    logger.info("Starting PubMed data collection...")

    # Initialize rate limiter for PubMed API (3 requests/second limit)
    rate_limiter = AdaptiveRateLimiter(
        RateLimitConfig(
            requests_per_second=3.0,
            requests_per_minute=100,
            burst_size=5,
            retry_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            circuit_failure_threshold=5,
            circuit_timeout=300.0,
        )
    )

    collector = PubMedDataCollector()

    # Use default search terms if not provided
    if search_terms is None:
        search_terms = [
            "CRISPR gene editing",
            "immunotherapy cancer",
            "genome sequencing",
        ]

    try:
        # Collect data for each search term with rate limiting
        for term in search_terms:
            logger.info(f"Collecting papers for search term: '{term}'")

            async def rate_limited_collect() -> None:
                await collector.collect_dataset(query=term, max_results=max_results)

            await rate_limiter.execute_with_retry(rate_limited_collect)

        # Load collected data to get statistics
        pubmed_data = load_pubmed_json()

        stats = {
            "papers_collected": len(pubmed_data.get("papers", [])),
            "citations_collected": len(pubmed_data.get("citation_network", {})),
            "search_terms": search_terms,
            "max_results_per_term": max_results,
            "timestamp": datetime.now().isoformat(),
            "rate_limiter_stats": rate_limiter.get_stats(),
        }

        logger.info(f"✅ PubMed collection complete: {stats['papers_collected']} papers")

        # Create artifact for tracking
        await create_markdown_artifact(
            key="pubmed-collection-report",
            markdown=f"""# PubMed Collection Report

## Summary
- **Papers Collected**: {stats['papers_collected']}
- **Citations**: {stats['citations_collected']}
- **Search Terms**: {', '.join(search_terms)}
- **Timestamp**: {stats['timestamp']}

## Rate Limiter Stats
- **Circuit State**: {stats['rate_limiter_stats']['circuit_state']}
- **Requests in Last Minute**: {stats['rate_limiter_stats']['requests_in_last_minute']}
- **Tokens Available**: {stats['rate_limiter_stats']['tokens_available']:.2f}
""",
            description="PubMed data collection statistics",
        )

        return stats

    except Exception as e:
        logger.error(f"❌ PubMed collection failed: {e}")
        raise


@task(
    name="collect_gene_data",
    description="Collect gene data linked to papers with rate limiting",
    retries=3,
    retry_delay_seconds=300,
    timeout_seconds=3600,
    tags=["data_collection", "genes"],
)
async def collect_gene_data() -> dict[str, Any]:
    """
    Collect gene data with adaptive rate limiting.

    Returns:
        Statistics about collected gene data
    """
    logger = get_run_logger()
    logger.info("Starting gene data collection...")

    # Initialize rate limiter for NCBI Gene API
    rate_limiter = AdaptiveRateLimiter(
        RateLimitConfig(
            requests_per_second=3.0,
            requests_per_minute=100,
            burst_size=5,
            retry_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
        )
    )

    collector = GeneDataCollector()

    try:
        # Collect gene data with rate limiting
        async def rate_limited_collect() -> None:
            await collector.collect_dataset()

        await rate_limiter.execute_with_retry(rate_limited_collect)

        # Load collected data to get statistics
        gene_data = load_gene_json()

        stats = {
            "genes_collected": len(gene_data.get("genes", [])),
            "timestamp": datetime.now().isoformat(),
            "rate_limiter_stats": rate_limiter.get_stats(),
        }

        logger.info(f"✅ Gene collection complete: {stats['genes_collected']} genes")

        # Create artifact
        await create_markdown_artifact(
            key="gene-collection-report",
            markdown=f"""# Gene Collection Report

## Summary
- **Genes Collected**: {stats['genes_collected']}
- **Timestamp**: {stats['timestamp']}

## Rate Limiter Stats
- **Circuit State**: {stats['rate_limiter_stats']['circuit_state']}
- **Requests in Last Minute**: {stats['rate_limiter_stats']['requests_in_last_minute']}
""",
            description="Gene data collection statistics",
        )

        return stats

    except Exception as e:
        logger.error(f"❌ Gene collection failed: {e}")
        raise


# ==================== GRAPH OPERATIONS ====================
@task(
    name="update_neo4j_graph",
    description="Update Neo4j graph with collected papers and genes",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=7200,  # 2 hour timeout
    tags=["graph", "neo4j"],
)
async def update_neo4j_graph(
    incremental: bool = True,
) -> dict[str, Any]:
    """
    Update Neo4j graph with papers and genes.

    Args:
        incremental: If True, use MERGE for upserts; if False, recreate graph

    Returns:
        Statistics about graph update
    """
    logger = get_run_logger()
    logger.info(f"Starting Neo4j graph update (incremental={incremental})...")

    # Load datasets
    pubmed_data = load_pubmed_json()
    gene_data = load_gene_json()

    paper_dataset = PaperDataset(**pubmed_data)
    gene_dataset = GeneDataset(**gene_data) if gene_data.get("genes") else None

    # Initialize Neo4j client
    client = await AsyncNeo4jClient.create()

    try:
        ingestion = Neo4jGraphIngestion(client)

        # If not incremental, clear existing data
        if not incremental:
            logger.warning("Clearing existing graph data...")
            await client.delete_graph()

        # Ingest papers (MERGE handles incremental updates)
        logger.info(f"Ingesting {len(paper_dataset.papers)} papers...")
        await ingestion.ingest_paper_dataset(paper_dataset)

        # Ingest genes if available
        if gene_dataset:
            logger.info(f"Ingesting {len(gene_dataset.genes)} genes...")
            await ingestion.ingest_genes(gene_dataset)

        # Get final counts
        stats = {
            "papers_ingested": len(paper_dataset.papers),
            "genes_ingested": len(gene_dataset.genes) if gene_dataset else 0,
            "citations_created": len(paper_dataset.citation_network),
            "total_authors": paper_dataset.metadata.total_authors,
            "total_mesh_terms": paper_dataset.metadata.total_mesh_terms,
            "incremental": incremental,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ Neo4j graph update complete: {stats}")

        # Create artifact
        await create_markdown_artifact(
            key="neo4j-update-report",
            markdown=f"""# Neo4j Graph Update Report

## Summary
- **Papers Ingested**: {stats['papers_ingested']}
- **Genes Ingested**: {stats['genes_ingested']}
- **Citations Created**: {stats['citations_created']}
- **Authors**: {stats['total_authors']}
- **MeSH Terms**: {stats['total_mesh_terms']}
- **Update Mode**: {'Incremental' if incremental else 'Full Rebuild'}
- **Timestamp**: {stats['timestamp']}
""",
            description="Neo4j graph update statistics",
        )

        return stats

    except Exception as e:
        logger.error(f"❌ Neo4j update failed: {e}")
        raise
    finally:
        await client.close()


# ==================== VECTOR STORE OPERATIONS ====================
@task(
    name="update_qdrant_vectors",
    description="Update Qdrant vector store with embeddings",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=7200,
    tags=["vectorstore", "qdrant"],
)
async def update_qdrant_vectors(
    recreate_collection: bool = False, batch_size: int = 50
) -> dict[str, Any]:
    """
    Update Qdrant vector store with paper embeddings.

    Args:
        recreate_collection: If True, delete and recreate collection
        batch_size: Batch size for embedding generation

    Returns:
        Statistics about vector store update
    """
    logger = get_run_logger()
    logger.info("Starting Qdrant vector store update...")

    # Initialize rate limiter for OpenAI API
    rate_limiter = AdaptiveRateLimiter(
        RateLimitConfig(
            requests_per_second=10.0,  # OpenAI allows higher rate
            requests_per_minute=500,
            burst_size=20,
            retry_attempts=5,
            base_delay=1.0,
            max_delay=30.0,
        )
    )

    vector_store = AsyncQdrantVectorStore()

    try:
        # Recreate collection if requested
        if recreate_collection:
            logger.warning("Recreating Qdrant collection...")
            try:
                await vector_store.delete_collection()
            except Exception:
                logger.debug("Collection didn't exist, skipping deletion")
            await vector_store.create_collection()

        # Load datasets
        pubmed_data = load_pubmed_json()
        gene_data = load_gene_json()

        papers_count = len(pubmed_data.get("papers", []))
        logger.info(f"Upserting {papers_count} papers to Qdrant...")

        # Wrap upsert with rate limiting
        async def rate_limited_upsert() -> None:
            await vector_store.upsert_points(pubmed_data, gene_data, batch_size)

        await rate_limiter.execute_with_retry(rate_limited_upsert)

        stats = {
            "papers_upserted": papers_count,
            "genes_attached": len(gene_data.get("genes", [])),
            "batch_size": batch_size,
            "collection_recreated": recreate_collection,
            "timestamp": datetime.now().isoformat(),
            "rate_limiter_stats": rate_limiter.get_stats(),
        }

        logger.info(f"✅ Qdrant update complete: {stats['papers_upserted']} papers")

        # Create artifact
        await create_markdown_artifact(
            key="qdrant-update-report",
            markdown=f"""# Qdrant Vector Store Update Report

## Summary
- **Papers Upserted**: {stats['papers_upserted']}
- **Genes Attached**: {stats['genes_attached']}
- **Batch Size**: {stats['batch_size']}
- **Collection Recreated**: {stats['collection_recreated']}
- **Timestamp**: {stats['timestamp']}

## Rate Limiter Stats
- **Circuit State**: {stats['rate_limiter_stats']['circuit_state']}
- **Requests in Last Minute**: {stats['rate_limiter_stats']['requests_in_last_minute']}
""",
            description="Qdrant vector store update statistics",
        )

        return stats

    except Exception as e:
        logger.error(f"❌ Qdrant update failed: {e}")
        raise
    finally:
        await vector_store.close()


# ==================== VALIDATION ====================
@task(
    name="validate_data_consistency",
    description="Validate consistency between data sources",
    retries=1,
    tags=["validation"],
)
async def validate_data_consistency() -> dict[str, Any]:
    """
    Validate data consistency across JSON, Neo4j, and Qdrant.

    Returns:
        Validation report with any inconsistencies
    """
    logger = get_run_logger()
    logger.info("Validating data consistency...")

    # Load JSON data
    pubmed_data = load_pubmed_json()
    json_paper_count = len(pubmed_data.get("papers", []))

    # Check Neo4j
    neo4j_client = await AsyncNeo4jClient.create()
    try:
        neo4j_count_result = await neo4j_client.query(
            "MATCH (p:Paper) RETURN count(p) as count"
        )
        neo4j_paper_count = neo4j_count_result[0]["count"] if neo4j_count_result else 0
    finally:
        await neo4j_client.close()

    # Check Qdrant
    qdrant_store = AsyncQdrantVectorStore()
    try:
        collection_info = await qdrant_store.client.get_collection(
            collection_name=qdrant_store.collection_name
        )
        qdrant_paper_count = collection_info.points_count
    finally:
        await qdrant_store.close()

    # Calculate differences
    inconsistencies = []
    if json_paper_count != neo4j_paper_count:
        inconsistencies.append(
            f"JSON ({json_paper_count}) != Neo4j ({neo4j_paper_count})"
        )
    if json_paper_count != qdrant_paper_count:
        inconsistencies.append(
            f"JSON ({json_paper_count}) != Qdrant ({qdrant_paper_count})"
        )

    validation_report = {
        "json_papers": json_paper_count,
        "neo4j_papers": neo4j_paper_count,
        "qdrant_papers": qdrant_paper_count,
        "is_consistent": len(inconsistencies) == 0,
        "inconsistencies": inconsistencies,
        "timestamp": datetime.now().isoformat(),
    }

    if validation_report["is_consistent"]:
        logger.info(
            f"✅ Data consistency validated: {json_paper_count} papers across all stores"
        )
    else:
        logger.warning(f"⚠️ Data inconsistencies detected: {inconsistencies}")

    # Create artifact
    await create_markdown_artifact(
        key="consistency-validation-report",
        markdown=f"""# Data Consistency Validation Report

## Paper Counts
- **JSON Files**: {json_paper_count}
- **Neo4j Graph**: {neo4j_paper_count}
- **Qdrant Vectors**: {qdrant_paper_count}

## Status
{'✅ **CONSISTENT** - All stores have matching counts' if validation_report['is_consistent'] else f"⚠️ **INCONSISTENT** - {', '.join(inconsistencies)}"}

**Timestamp**: {validation_report['timestamp']}
""",
        description="Data consistency validation results",
    )

    return validation_report
