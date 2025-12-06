"""Quick script to run flows and see them in Prefect UI."""

import asyncio

from biomedical_graphrag.orchestration.flows import incremental_update, consistency_check


async def main():
    """Run a flow."""
    print("=" * 60)
    print("Running flow - watch it in Prefect UI!")
    print("http://localhost:4200/runs")
    print("=" * 60)
    print()

    # Run incremental update with small dataset for testing
    result = await incremental_update(
        search_terms=["CRISPR"],
        max_results_per_term=10,  # Small for testing
        batch_size=10,
    )

    print()
    print("✅ Flow completed!")
    print("Check the Prefect UI for:")
    print("  - Flow run details")
    print("  - Task execution graph")
    print("  - Generated artifacts")
    print("  - Logs and timing")


if __name__ == "__main__":
    asyncio.run(main())
