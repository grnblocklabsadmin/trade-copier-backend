# Trade Copier Backend

Multi-exchange crypto trade copier backend built with FastAPI.

The system is designed to execute synchronized trades across multiple exchange accounts with unified risk management, execution logging, and safety validation.

This project is being developed as a staged trading infrastructure backend.

---

# System Architecture

The system follows a modular trading infrastructure architecture.

Execution pipeline:


API
→ Copier Router
→ Execution Engine
→ Exchange Client Service
→ Exchange Adapter
→ OrderExecutionResult
→ Execution Logs


This pipeline is the core of the system and must remain stable.

---

# Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Poetry
- Docker

Environment: WSL2 Linux

---

# Project Structure


app/

api/
router.py
deps.py
guards.py
routes/

core/
config.py
risk.py
trading.py

db/
session.py

models/
execution_log.py

schemas/
copier.py

services/
exchange_client_service.py
trade_copier_service.py
trade_copier_execution_engine.py
execution_log_service.py

sizing/
position_sizing.py

exchanges/
base.py


---

# Core System Components

## Trade Copier Execution Engine

Responsible for dispatching trades across multiple accounts.

Handles:

- account iteration
- execution orchestration
- order dispatch
- result aggregation

---

## Exchange Client Service

Provides abstraction layer for exchange integrations.

Planned adapters:

- Binance
- Bybit
- OKX

---

## Position Sizing Engine

Risk-based position sizing.

Inputs:

- available balance
- risk percent
- leverage
- current price
- exchange limits

Outputs:

- allocated margin
- target notional
- raw quantity
- rounded quantity
- final notional

---

## Risk Engine

Validates dispatch parameters before execution.

Limits:

- max risk percent
- max leverage
- max accounts per dispatch
- duplicate account protection

Example limits:


max_risk_percent = 0.05
max_leverage = 20
max_accounts_per_dispatch = 20


---

# Execution Logging

All execution attempts are logged in PostgreSQL.

Table:


execution_logs


Fields:


id
run_id
event_type
symbol
side
account_id
exchange
status
message
payload_json
created_at


Logs allow full audit trail of trading activity.

---

# Run ID Batching

Each dispatch generates a `run_id`.

Example:


run_id: 8123af50-38e3-4626-b75c-eec68e239e70


All orders belonging to the same dispatch share the same run_id.

This allows tracking of multi-account execution batches.

---

# Execution Modes

Current mode:


SIMULATED


Orders are validated and logged but not sent to exchanges.

Planned mode:


LIVE


Real order placement via exchange APIs.

---

# API Endpoints

## Execution Planning


POST /api/v1/copier/execute


Calculates position sizes for accounts.

---

## Manual Execution Planning


POST /api/v1/copier/execute/manual


Allows manual input of account parameters.

---

## Dispatch


POST /api/v1/copier/dispatch


Executes copier dispatch using stored accounts.

---

## Manual Dispatch


POST /api/v1/copier/dispatch/manual


Executes dispatch using manually supplied account parameters.

---

## Execution History


GET /api/v1/execution/history


Query execution logs.

Filters:

- run_id
- account_id
- exchange
- symbol
- pagination

---

# Current Development Stage

Stage 5 — Live-Ready Trading Infrastructure

Completed systems:

- position sizing engine
- multi-account dispatch
- exchange abstraction
- execution logging
- run_id batching
- risk engine
- side normalization
- manual dispatch simulation
- execution history API

---

# Next Development Stage

Stage 6 — Operational Live Dispatch Foundation

Planned implementation:

- strict order request validation
- symbol validation
- quantity validation
- exchange limit validation
- live order execution
- exchange adapters
- execution error handling
- real execution logging

---

# Development Rules

The execution pipeline must not be redesigned.

Stable modules:


trade_copier_execution_engine
exchange_client_service
execution_log_service
position_sizing
risk engine


These modules must only be extended, not rewritten.

---

# Project Goal

Build a reliable multi-exchange trade copier capable of safely executing synchronized trades across multiple accounts with strict risk management and full execution traceability.

This backend will support:

- multi-account trade mirroring
- unified risk management
- exchange abstraction
- execution audit trail
- scalable trading infrastructure.