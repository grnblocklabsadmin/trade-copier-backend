# Trade Copier Backend

Multi-exchange crypto trade copier backend.

## Tech stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Poetry

## Features

- multi-account dispatch
- risk engine
- position sizing
- execution logging
- run_id batching
- exchange abstraction

## Execution Pipeline

API
→ Copier Router
→ Execution Engine
→ Exchange Client
→ Exchange Adapter
→ OrderExecutionResult
→ Execution Logs