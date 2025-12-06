# Project Structure

Clean, organized structure for the biomedical GraphRAG pipeline.

## Directory Layout

```
biomedical-graphrag/
├── .github/                    # GitHub workflows and templates
├── data/                       # Dataset storage (PubMed, Gene data)
│   ├── pubmed_dataset.json
│   └── gene_dataset.json
│
├── deployment/                 # Deployment configuration
│   ├── docker-compose.prefect.yml  # Prefect infrastructure
│   ├── Dockerfile.prefect          # Worker container
│   └── README.md
│
├── docs/                       # Documentation
│   ├── ORCHESTRATION.md            # Full orchestration guide
│   └── QUICKSTART_ORCHESTRATION.md # Quick start guide
│
├── scripts/                    # Utility scripts
│   ├── deploy_flows.py            # Deploy Prefect flows
│   ├── run_flow.py                # Test flow execution
│   └── README.md
│
├── src/biomedical_graphrag/   # Main source code
│   ├── application/               # Application layer
│   │   ├── cli/                   # CLI interfaces
│   │   └── services/              # Business logic
│   │
│   ├── data_sources/              # Data collection
│   │   ├── gene/                  # Gene data collector
│   │   └── pubmed/                # PubMed data collector
│   │
│   ├── domain/                    # Domain models
│   │   ├── author.py
│   │   ├── citation.py
│   │   ├── dataset.py
│   │   ├── gene.py
│   │   ├── meshterm.py
│   │   └── paper.py
│   │
│   ├── infrastructure/            # Infrastructure adapters
│   │   ├── neo4j_db/              # Neo4j graph database
│   │   └── qdrant_db/             # Qdrant vector store
│   │
│   ├── orchestration/             # Prefect workflows ⭐ NEW
│   │   ├── flows.py               # Main orchestration flows
│   │   ├── tasks.py               # Prefect tasks
│   │   └── rate_limiter.py        # Rate limiting logic
│   │
│   ├── utils/                     # Utility modules
│   │   ├── json_util.py
│   │   └── logger_util.py
│   │
│   └── config.py                  # Configuration management
│
├── static/                     # Static assets
├── tests/                      # Test suite
│   ├── integration/
│   └── unit/
│
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── .gitignore
├── LICENSE
├── Makefile                    # Build and dev commands
├── prefect.yaml                # Prefect configuration
├── PROJECT_STRUCTURE.md        # This file
├── pyproject.toml              # Project metadata & dependencies
├── README.md                   # Main documentation
└── uv.lock                     # Locked dependencies
```

## Key Components

### Source Code (`src/biomedical_graphrag/`)

**Application Layer**
- CLI interfaces for data collection and querying
- Service classes for hybrid queries

**Data Sources**
- PubMed API client and collector
- Gene API client and collector
- Base class with rate limiting

**Domain Models**
- Pydantic models for type safety
- Paper, Author, Gene, Citation, MeSHTerm

**Infrastructure**
- Neo4j async client and graph schema
- Qdrant async client and vector operations

**Orchestration** ⭐
- Prefect flows with task dependencies
- Rate limiter with circuit breaker
- Weekly/monthly scheduled updates

**Utils**
- JSON loading/saving
- Structured logging with Loguru

### Configuration

**Environment Variables (`.env`)**
- API keys (OpenAI, PubMed, Qdrant)
- Database URIs (Neo4j, Qdrant)
- Email for PubMed API

**Prefect Configuration (`prefect.yaml`)**
- Work pool settings
- Deployment defaults

**Project Configuration (`pyproject.toml`)**
- Dependencies and dev tools
- Ruff, mypy, pytest settings

### Deployment

**Docker Setup**
- Prefect server + PostgreSQL + Worker
- Containerized execution environment

**Scripts**
- Deployment automation
- Testing utilities

### Documentation

**Main Docs**
- `README.md` - Getting started
- `docs/ORCHESTRATION.md` - Full orchestration guide
- `docs/QUICKSTART_ORCHESTRATION.md` - Quick start

**Component Docs**
- Each directory has README.md where needed

## Development Workflow

1. **Setup**: `uv sync --all-groups`
2. **Data Collection**: `make pubmed-data-collector-run`
3. **Create Graph**: `make create-graph`
4. **Create Vectors**: `make ingest-qdrant-data`
5. **Query**: `make custom-graph-query QUESTION="your question"`

## Orchestration Workflow

1. **Start Server**: `make prefect-server-start`
2. **Deploy Flows**: `uv run python scripts/deploy_flows.py`
3. **Start Worker**: `make prefect-worker-start`
4. **Trigger from UI**: http://localhost:4200

## Testing

```bash
# All tests
make tests

# Type checking
make mypy

# Linting
make ruff-check

# Format
make ruff-format-fix
```

## Clean Architecture

The project follows clean architecture principles:

1. **Domain Layer** (innermost)
   - Pure business logic
   - No external dependencies

2. **Application Layer**
   - Use cases and services
   - Orchestrates domain objects

3. **Infrastructure Layer** (outermost)
   - External integrations
   - Databases, APIs, etc.

**Dependency Rule**: Dependencies point inward only.

## Adding New Features

1. **New Data Source**: Add to `src/biomedical_graphrag/data_sources/`
2. **New Domain Model**: Add to `src/biomedical_graphrag/domain/`
3. **New Query Type**: Add to `src/biomedical_graphrag/application/services/`
4. **New Orchestration**: Add task to `orchestration/tasks.py`

## Best Practices

- ✅ Use async/await throughout
- ✅ Type hints on all functions
- ✅ Pydantic for data validation
- ✅ Structured logging
- ✅ Rate limiting on external APIs
- ✅ Error handling with retries
- ✅ Tests for critical paths
