# Scripts

Utility scripts for development and deployment.

## Files

### `deploy_flows.py`
Deploy Prefect flows to the server (Prefect 3.x compatible).

**Usage:**
```bash
python scripts/deploy_flows.py
```

### `run_flow.py`
Quick test script to run a flow with small dataset.

**Usage:**
```bash
python scripts/run_flow.py
# Or via Makefile:
make prefect-test-rate-limit
```

## Notes

- These scripts are for development/testing
- Production deployments should use `prefect deploy` CLI
- See `docs/ORCHESTRATION.md` for detailed orchestration guide
