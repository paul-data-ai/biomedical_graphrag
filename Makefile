# Makefile

# Check if .env exists
ifeq (,$(wildcard .env))
$(error .env file is missing at .env. Please create one based on .env.example)
endif

# Load environment variables from .env
include .env

.PHONY: tests mypy clean help ruff-check ruff-check-fix ruff-format ruff-format-fix all-check all-fix

QUESTION ?=

#################################################################################
## Data Collector Commands
#################################################################################

pubmed-data-collector-run: ## Run the data collector
	@echo "Running data collector..."
	uv run src/biomedical_graphrag/data_sources/pubmed/pubmed_data_collector.py
	@echo "Data collector run complete."

gene-data-collector-run: ## Run the data collector
	@echo "Running data collector..."
	uv run src/biomedical_graphrag/data_sources/gene/gene_data_collector.py
	@echo "Data collector run complete."

#################################################################################
## Neo4j Graph Commands
#################################################################################

create-graph: ## Create the Neo4j graph from the dataset
	@echo "Creating Neo4j graph from dataset..."
	uv run src/biomedical_graphrag/infrastructure/neo4j_db/create_graph.py
	@echo "Neo4j graph creation complete."

delete-graph: ## Delete all nodes and relationships in the Neo4j graph
	@echo "Deleting all nodes and relationships in the Neo4j graph..."
	uv run src/biomedical_graphrag/infrastructure/neo4j_db/delete_graph.py
	@echo "Neo4j graph deletion complete."

example-graph-query: ## Run example queries on the Neo4j graph using GraphRAG
	@echo "Running example queries on the Neo4j graph..."
	uv run src/biomedical_graphrag/application/cli/fusion_query.py --examples
	@echo "Example queries complete."

custom-graph-query: ## Run a custom natural language query using Neo4j GraphRAG (use QUESTION="your question")
	@echo "Running custom query on the Neo4j graph with GraphRAG..."
	uv run src/biomedical_graphrag/application/cli/fusion_query.py $(if $(QUESTION),--ask "$(QUESTION)")
	@echo "Custom query complete."

#################################################################################
## Qdrant Commands
#################################################################################
create-qdrant-collection: ## Create the Qdrant collection for embeddings
	@echo "Creating Qdrant collection for embeddings..."
	uv run src/biomedical_graphrag/infrastructure/qdrant_db/create_collection.py
	@echo "Qdrant collection creation complete."

delete-qdrant-collection: ## Delete the Qdrant collection for embeddings
	@echo "Deleting Qdrant collection for embeddings..."
	uv run src/biomedical_graphrag/infrastructure/qdrant_db/delete_collection.py
	@echo "Qdrant collection deletion complete."

ingest-qdrant-data: ## Ingest embeddings into the Qdrant collection
	@echo "Ingesting embeddings into the Qdrant collection..."
	uv run src/biomedical_graphrag/infrastructure/qdrant_db/qdrant_ingestion.py
	@echo "Embeddings ingestion complete."

custom-qdrant-query: ## Run a custom query on the Qdrant collection (modify the --ask parameter as needed)
	@echo "Running custom query on the Qdrant collection..."
	uv run src/biomedical_graphrag/application/cli/query_vectorstore.py $(if $(QUESTION),--ask "$(QUESTION)")
	@echo "Custom query complete."

#################################################################################
## Testing
#################################################################################

tests: ## Run all tests
	@echo "Running all tests..."
	uv run pytest
	@echo "All tests completed."

################################################################################
## Prek Commands
################################################################################

prek-run: ## Run prek hooks
	@echo "Running prek hooks..."
	prek run --all-files
	@echo "Prek checks complete."

################################################################################
## Linting
################################################################################

# Linting (just checks)
ruff-check: ## Check code lint violations (--diff to show possible changes)
	@echo "Checking Ruff formatting..."
	uv run ruff check .
	@echo "Ruff lint checks complete."

ruff-check-fix: ## Auto-format code using Ruff
	@echo "Formatting code with Ruff..."
	uv run ruff check . --fix --exit-non-zero-on-fix
	@echo "Formatting complete."

################################################################################
## Formatting
################################################################################

# Formatting (just checks)
ruff-format: ## Check code format violations (--diff to show possible changes)
	@echo "Checking Ruff formatting..."
	uv run ruff format . --check
	@echo "Ruff format checks complete."

ruff-format-fix: ## Auto-format code using Ruff
	@echo "Formatting code with Ruff..."
	uv run ruff format .
	@echo "Formatting complete."

#################################################################################
## Static Type Checking
#################################################################################

mypy: ## Run MyPy static type checker
	@echo "Running MyPy static type checker..."
	uv run mypy
	@echo "MyPy static type checker complete."

################################################################################
## Cleanup
################################################################################

clean: ## Clean up cached generated files
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

################################################################################
## Composite Commands
################################################################################

all-check: ruff-format ruff-check clean ## Run all: linting, formatting and type checking

all-fix: ruff-format-fix ruff-check-fix mypy clean ## Run all fix: auto-formatting and linting fixes

################################################################################
## Prefect Orchestration - LOCAL (Recommended for Development/Tutorial)
################################################################################

prefect-local-start: ## Start local Prefect server (no Docker required)
	@echo "Starting local Prefect server..."
	@echo "UI will be available at http://localhost:4200"
	uv run prefect server start

prefect-local-deploy: ## Deploy flows to local Prefect server
	@echo "Deploying flows to local Prefect server..."
	uv run python scripts/deploy_local.py

prefect-local-worker: ## Start local Prefect worker (run in separate terminal)
	@echo "Starting local Prefect worker..."
	@echo "Make sure Prefect server is running first!"
	uv run prefect worker start --pool default

prefect-local-trigger-incremental: ## Manually trigger incremental update (local)
	@echo "Triggering incremental update..."
	uv run prefect deployment run incremental_update/weekly-incremental

prefect-local-trigger-rebuild: ## Manually trigger full rebuild (local)
	@echo "Triggering full rebuild..."
	uv run prefect deployment run full_rebuild/full-rebuild

prefect-local-trigger-validation: ## Manually trigger consistency check (local)
	@echo "Triggering consistency validation..."
	uv run prefect deployment run consistency_check/daily-validation

################################################################################
## Prefect Orchestration - DOCKER (For Production)
################################################################################

prefect-server-start: ## Start Prefect server with Docker Compose
	@echo "Starting Prefect server..."
	docker-compose -f deployment/docker-compose.prefect.yml up -d
	@echo "Prefect UI available at http://localhost:4200"

prefect-server-stop: ## Stop Prefect server
	@echo "Stopping Prefect server..."
	docker-compose -f deployment/docker-compose.prefect.yml down

prefect-server-logs: ## View Prefect server logs
	docker-compose -f deployment/docker-compose.prefect.yml logs -f

prefect-deploy: ## Deploy Prefect flows
	@echo "Deploying Prefect flows from worker container..."
	docker exec biomedical-prefect-worker uv run prefect deploy --all
	@echo "Deployment complete."

prefect-worker-start: ## Start Prefect worker locally (without Docker)
	@echo "Starting Prefect worker..."
	uv run prefect worker start --pool biomedical-pool

prefect-run-incremental: ## Manually trigger incremental update
	@echo "Triggering incremental update..."
	uv run prefect deployment run biomedical-graphrag-incremental-update/weekly-incremental

prefect-run-rebuild: ## Manually trigger full rebuild
	@echo "Triggering full rebuild..."
	uv run prefect deployment run biomedical-graphrag-full-rebuild/monthly-rebuild

prefect-test-rate-limit: ## Test rate limiting with small dataset
	@echo "Testing rate limiting..."
	uv run python scripts/run_flow.py

################################################################################
## API Server
################################################################################

api-start: ## Start the FastAPI server
	@echo "Starting FastAPI server on http://localhost:8000..."
	uv run uvicorn biomedical_graphrag.api.main:app --host 0.0.0.0 --port 8000 --reload

api-start-prod: ## Start the FastAPI server in production mode
	@echo "Starting FastAPI server in production mode..."
	uv run uvicorn biomedical_graphrag.api.main:app --host 0.0.0.0 --port 8000 --workers 4

################################################################################
## Help
################################################################################

help: ## Display this help message
	@echo "Default target: $(.DEFAULT_GOAL)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
