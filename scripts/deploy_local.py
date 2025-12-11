"""Deploy flows to local Prefect server."""

import asyncio

from biomedical_graphrag.orchestration.flows import (
    consistency_check,
    full_rebuild,
    incremental_update,
)


async def deploy_to_local_server() -> None:
    """Deploy all flows to local Prefect server."""

    print("🚀 Deploying flows to LOCAL Prefect server...")
    print("=" * 60)
    print("Make sure Prefect server is running: prefect server start")
    print("=" * 60)
    print()

    # Deploy incremental update with schedule
    deployment1 = await incremental_update.to_deployment(
        name="daily-incremental",
        work_pool_name="default",
        cron="0 2 * * *",  # Every day at 2 AM
        parameters={
            "search_terms": ["CRISPR gene editing", "cancer immunotherapy"],
            "max_results_per_term": 50,
            "batch_size": 50,
        },
        tags=["biomedical", "incremental", "scheduled"],
        description="Daily incremental update - runs every day at 2 AM",
    )
    deployment_id1 = await deployment1.apply()
    print(f"✅ Deployed: incremental_update/daily-incremental")
    print(f"   Schedule: Every day at 2 AM")
    print(f"   ID: {deployment_id1}")
    print()

    # Deploy weekly incremental (for manual trigger)
    deployment2 = await incremental_update.to_deployment(
        name="weekly-incremental",
        work_pool_name="default",
        parameters={
            "search_terms": ["CRISPR gene editing", "cancer immunotherapy", "genome sequencing"],
            "max_results_per_term": 100,
            "batch_size": 50,
        },
        tags=["biomedical", "incremental", "manual"],
        description="Weekly incremental update - trigger manually",
    )
    deployment_id2 = await deployment2.apply()
    print(f"✅ Deployed: incremental_update/weekly-incremental")
    print(f"   Trigger: Manual")
    print(f"   ID: {deployment_id2}")
    print()

    # Deploy full rebuild (manual trigger only)
    deployment3 = await full_rebuild.to_deployment(
        name="full-rebuild",
        work_pool_name="default",
        parameters={
            "search_terms": [
                "CRISPR gene editing",
                "cancer immunotherapy",
                "genome sequencing",
                "CAR-T cell therapy",
                "mRNA vaccine",
            ],
            "max_results_per_term": 200,
            "batch_size": 50,
        },
        tags=["biomedical", "full-rebuild", "manual"],
        description="Full rebuild - trigger manually when needed",
    )
    deployment_id3 = await deployment3.apply()
    print(f"✅ Deployed: full_rebuild/full-rebuild")
    print(f"   Trigger: Manual")
    print(f"   ID: {deployment_id3}")
    print()

    # Deploy consistency check with daily schedule
    deployment4 = await consistency_check.to_deployment(
        name="daily-validation",
        work_pool_name="default",
        cron="0 1 * * *",  # Every day at 1 AM
        tags=["biomedical", "validation", "scheduled"],
        description="Daily data consistency check - runs every day at 1 AM",
    )
    deployment_id4 = await deployment4.apply()
    print(f"✅ Deployed: consistency_check/daily-validation")
    print(f"   Schedule: Every day at 1 AM")
    print(f"   ID: {deployment_id4}")
    print()

    print("=" * 60)
    print("✅ All flows deployed successfully!")
    print()
    print("📍 Next steps:")
    print("1. View deployments in UI: http://localhost:4200/deployments")
    print()
    print("2. Start a worker to execute flows:")
    print("   uv run prefect worker start --pool default")
    print()
    print("3. Trigger a flow manually:")
    print("   uv run prefect deployment run incremental_update/weekly-incremental")
    print()


if __name__ == "__main__":
    asyncio.run(deploy_to_local_server())
