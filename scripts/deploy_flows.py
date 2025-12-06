"""Deploy flows to Prefect server so they can be triggered from UI."""

import asyncio

from biomedical_graphrag.orchestration.flows import (
    consistency_check,
    full_rebuild,
    incremental_update,
)


async def deploy_all() -> None:
    """Deploy all flows to Prefect server."""

    print("🚀 Deploying flows to Prefect server...")
    print("=" * 60)

    # Deploy incremental update (can be triggered manually from UI)
    await incremental_update.deploy(
        name="weekly-incremental-update",
        work_pool_name="biomedical-pool",
        cron="0 2 * * 0",  # Every Sunday at 2 AM UTC
        parameters={
            "search_terms": ["CRISPR"],
            "max_results_per_term": 10,
            "batch_size": 10,
        },
        tags=["biomedical", "incremental", "production"],
        description="Weekly incremental update - can be triggered manually from UI",
    )
    print("✅ Deployed: weekly-incremental-update")
    print("   Schedule: Every Sunday at 2 AM UTC")
    print("   Can trigger manually from UI!")
    print()

    # Deploy full rebuild (manual trigger only)
    await full_rebuild.deploy(
        name="manual-full-rebuild",
        work_pool_name="biomedical-pool",
        parameters={
            "search_terms": ["CRISPR"],
            "max_results_per_term": 20,
            "batch_size": 10,
        },
        tags=["biomedical", "full-rebuild", "manual"],
        description="Full rebuild - trigger manually from UI when needed",
    )
    print("✅ Deployed: manual-full-rebuild")
    print("   Trigger: Manual from UI")
    print()

    # Deploy consistency check (manual trigger)
    await consistency_check.deploy(
        name="manual-consistency-check",
        work_pool_name="biomedical-pool",
        tags=["biomedical", "validation", "manual"],
        description="Data consistency check - trigger manually from UI",
    )
    print("✅ Deployed: manual-consistency-check")
    print("   Trigger: Manual from UI")
    print()

    print("=" * 60)
    print("✅ All flows deployed successfully!")
    print()
    print("📍 Next steps:")
    print("1. Start a worker:")
    print("   uv run prefect worker start --pool biomedical-pool")
    print()
    print("2. Go to Prefect UI: http://localhost:4200/deployments")
    print()
    print("3. Click on any deployment → Click 'Run' button")
    print()


if __name__ == "__main__":
    asyncio.run(deploy_all())
