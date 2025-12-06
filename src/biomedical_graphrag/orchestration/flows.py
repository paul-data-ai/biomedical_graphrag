"""Main Prefect flows for biomedical GraphRAG orchestration."""

from datetime import datetime
from typing import Any

from prefect import flow, get_run_logger
from prefect.artifacts import create_markdown_artifact

from biomedical_graphrag.orchestration.tasks import (
    collect_gene_data,
    collect_pubmed_data,
    update_neo4j_graph,
    update_qdrant_vectors,
    validate_configuration,
    validate_data_consistency,
)


@flow(
    name="biomedical-graphrag-full-pipeline",
    description="Complete pipeline: data collection, graph building, and vector indexing",
    version="1.0.0",
    log_prints=True,
)
async def full_pipeline(
    search_terms: list[str] | None = None,
    max_results_per_term: int = 100,
    incremental_graph_update: bool = True,
    recreate_vector_collection: bool = False,
    batch_size: int = 50,
) -> dict[str, Any]:
    """
    Execute the complete biomedical GraphRAG pipeline with clear task dependencies.

    Task Dependency Flow:
    1. validate_configuration
       ↓
    2. collect_pubmed_data ──┐
       ↓                     │
    3. collect_gene_data ────┤
       ↓                     │
    4. update_neo4j_graph ←──┘
       ↓
    5. update_qdrant_vectors
       ↓
    6. validate_data_consistency

    Args:
        search_terms: List of PubMed search terms (optional)
        max_results_per_term: Maximum results per search term
        incremental_graph_update: Use MERGE for incremental updates
        recreate_vector_collection: Recreate Qdrant collection
        batch_size: Batch size for embedding generation

    Returns:
        Pipeline execution statistics
    """
    logger = get_run_logger()
    pipeline_start = datetime.now()

    logger.info("🚀 Starting Biomedical GraphRAG Pipeline")
    logger.info(f"Configuration: incremental={incremental_graph_update}, "
                f"recreate_vectors={recreate_vector_collection}")

    try:
        # Step 1: Validate configuration (must succeed before anything else)
        logger.info("Step 1/6: Validating configuration...")
        config_validation = await validate_configuration()

        # Step 2: Collect PubMed data (depends on validation)
        logger.info("Step 2/6: Collecting PubMed data...")
        pubmed_stats = await collect_pubmed_data(
            search_terms=search_terms, max_results=max_results_per_term
        )

        # Step 3: Collect gene data (depends on PubMed data being collected)
        logger.info("Step 3/6: Collecting gene data...")
        gene_stats = await collect_gene_data()

        # Step 4: Update Neo4j graph (depends on both PubMed and gene data)
        logger.info("Step 4/6: Updating Neo4j graph...")
        neo4j_stats = await update_neo4j_graph(incremental=incremental_graph_update)

        # Step 5: Update Qdrant vectors (depends on data collection, runs after graph)
        logger.info("Step 5/6: Updating Qdrant vector store...")
        qdrant_stats = await update_qdrant_vectors(
            recreate_collection=recreate_vector_collection, batch_size=batch_size
        )

        # Step 6: Validate consistency (depends on all updates being complete)
        logger.info("Step 6/6: Validating data consistency...")
        validation_report = await validate_data_consistency()

        # Calculate pipeline duration
        pipeline_duration = (datetime.now() - pipeline_start).total_seconds()

        # Compile final statistics
        pipeline_stats = {
            "status": "success",
            "duration_seconds": pipeline_duration,
            "config_validation": config_validation,
            "pubmed_collection": pubmed_stats,
            "gene_collection": gene_stats,
            "neo4j_update": neo4j_stats,
            "qdrant_update": qdrant_stats,
            "validation": validation_report,
            "timestamp": datetime.now().isoformat(),
        }

        # Create final summary artifact
        await create_markdown_artifact(
            key="pipeline-execution-summary",
            markdown=f"""# Pipeline Execution Summary

## Status: {'✅ SUCCESS' if validation_report['is_consistent'] else '⚠️ COMPLETED WITH WARNINGS'}

**Duration**: {pipeline_duration:.2f} seconds ({pipeline_duration/60:.2f} minutes)

## Data Collection
- **PubMed Papers**: {pubmed_stats['papers_collected']}
- **Genes**: {gene_stats['genes_collected']}

## Graph Update
- **Papers in Neo4j**: {neo4j_stats['papers_ingested']}
- **Genes in Neo4j**: {neo4j_stats['genes_ingested']}
- **Citations**: {neo4j_stats['citations_created']}
- **Update Mode**: {'Incremental' if incremental_graph_update else 'Full Rebuild'}

## Vector Store Update
- **Vectors in Qdrant**: {qdrant_stats['papers_upserted']}
- **Collection Recreated**: {recreate_vector_collection}

## Validation
- **JSON Papers**: {validation_report['json_papers']}
- **Neo4j Papers**: {validation_report['neo4j_papers']}
- **Qdrant Vectors**: {validation_report['qdrant_papers']}
- **Consistency**: {'✅ Pass' if validation_report['is_consistent'] else '⚠️ Fail'}

{f"**Inconsistencies**: {', '.join(validation_report['inconsistencies'])}" if not validation_report['is_consistent'] else ''}

**Completed**: {pipeline_stats['timestamp']}
""",
            description="Complete pipeline execution summary",
        )

        logger.info(f"✅ Pipeline completed successfully in {pipeline_duration:.2f}s")
        return pipeline_stats

    except Exception as e:
        pipeline_duration = (datetime.now() - pipeline_start).total_seconds()
        logger.error(f"❌ Pipeline failed after {pipeline_duration:.2f}s: {e}")

        # Create failure artifact
        await create_markdown_artifact(
            key="pipeline-failure-report",
            markdown=f"""# Pipeline Execution Failed

## Error
```
{str(e)}
```

**Duration before failure**: {pipeline_duration:.2f} seconds
**Timestamp**: {datetime.now().isoformat()}

Please check the logs for detailed error information.
""",
            description="Pipeline execution failure report",
        )

        raise


@flow(
    name="biomedical-graphrag-incremental-update",
    description="Incremental update: data collection and upsert to stores",
    version="1.0.0",
    log_prints=True,
)
async def incremental_update(
    search_terms: list[str] | None = None,
    max_results_per_term: int = 50,
    batch_size: int = 50,
) -> dict[str, Any]:
    """
    Execute incremental update (for weekly scheduled runs).

    This is optimized for regular updates with:
    - Smaller max_results (focus on recent papers)
    - Incremental graph updates (MERGE)
    - Upsert to vector store (no recreation)

    Args:
        search_terms: List of PubMed search terms
        max_results_per_term: Maximum results per search term
        batch_size: Batch size for embedding generation

    Returns:
        Update statistics
    """
    return await full_pipeline(
        search_terms=search_terms,
        max_results_per_term=max_results_per_term,
        incremental_graph_update=True,  # Use MERGE
        recreate_vector_collection=False,  # Upsert only
        batch_size=batch_size,
    )


@flow(
    name="biomedical-graphrag-full-rebuild",
    description="Full rebuild: recreate all stores from scratch",
    version="1.0.0",
    log_prints=True,
)
async def full_rebuild(
    search_terms: list[str] | None = None,
    max_results_per_term: int = 200,
    batch_size: int = 50,
) -> dict[str, Any]:
    """
    Execute full rebuild (for monthly/quarterly deep refresh).

    This recreates everything from scratch:
    - Larger max_results
    - Full graph rebuild
    - Recreate vector collection

    Args:
        search_terms: List of PubMed search terms
        max_results_per_term: Maximum results per search term
        batch_size: Batch size for embedding generation

    Returns:
        Rebuild statistics
    """
    logger = get_run_logger()
    logger.warning("⚠️ Running FULL REBUILD - this will recreate all data stores")

    return await full_pipeline(
        search_terms=search_terms,
        max_results_per_term=max_results_per_term,
        incremental_graph_update=False,  # Full rebuild
        recreate_vector_collection=True,  # Recreate collection
        batch_size=batch_size,
    )


@flow(
    name="validate-consistency",
    description="Validate data consistency across all stores",
    version="1.0.0",
)
async def consistency_check() -> dict[str, Any]:
    """
    Run standalone consistency validation.

    Returns:
        Validation report
    """
    logger = get_run_logger()
    logger.info("Running consistency validation...")

    validation_report = await validate_data_consistency()

    if validation_report["is_consistent"]:
        logger.info("✅ All stores are consistent")
    else:
        logger.warning(f"⚠️ Inconsistencies found: {validation_report['inconsistencies']}")

    return validation_report


# ==================== UTILITY FLOWS ====================
@flow(
    name="test-rate-limiting",
    description="Test rate limiting configuration",
    version="1.0.0",
)
async def test_rate_limiting() -> dict[str, Any]:
    """
    Test flow to verify rate limiting works correctly.

    Returns:
        Rate limiter statistics
    """
    logger = get_run_logger()
    logger.info("Testing rate limiting with small data collection...")

    # Collect small amount of data to test rate limiting
    pubmed_stats = await collect_pubmed_data(
        search_terms=["CRISPR"], max_results=10
    )

    logger.info("✅ Rate limiting test complete")
    return pubmed_stats


if __name__ == "__main__":
    import asyncio

    # Run incremental update when executed directly
    asyncio.run(incremental_update())
