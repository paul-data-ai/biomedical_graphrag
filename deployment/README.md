# Deployment

Docker and deployment configuration files for the biomedical GraphRAG pipeline.

## Files

### `docker-compose.prefect.yml`
Docker Compose configuration for running Prefect infrastructure:
- Prefect server (UI on port 4200)
- PostgreSQL database (metadata storage)
- Prefect worker (task execution)

**Usage:**
```bash
# Start all services
docker-compose -f deployment/docker-compose.prefect.yml up -d

# Stop services
docker-compose -f deployment/docker-compose.prefect.yml down

# View logs
docker-compose -f deployment/docker-compose.prefect.yml logs -f
```

Or use Makefile commands:
```bash
make prefect-server-start
make prefect-server-stop
make prefect-server-logs
```

### `Dockerfile.prefect`
Dockerfile for the Prefect worker container.

Includes:
- Python 3.13
- uv for dependency management
- All project dependencies
- Source code

## Environment Variables

Required in `.env` file:
- `OPENAI__API_KEY` - OpenAI API key
- `NEO4J__URI` - Neo4j connection URI
- `NEO4J__USERNAME` - Neo4j username
- `NEO4J__PASSWORD` - Neo4j password
- `QDRANT__URL` - Qdrant URL
- `QDRANT__API_KEY` - Qdrant API key
- `PUBMED__EMAIL` - Email for PubMed API
- `PUBMED__API_KEY` - Optional PubMed API key

## Production Deployment

For production, consider:
1. **Prefect Cloud** instead of self-hosted server
2. **Kubernetes** for container orchestration
3. **Secrets management** (AWS Secrets Manager, Vault, etc.)
4. **Monitoring** (Prometheus, Grafana)

See `docs/ORCHESTRATION.md` for production deployment guide.
