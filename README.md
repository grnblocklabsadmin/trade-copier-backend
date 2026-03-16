# Trade Copier Backend

Multi-exchange crypto trade copier backend built with FastAPI.

The system is designed to execute synchronized trades across multiple exchange accounts with unified risk management, execution logging, and safety validation.

This project is being developed as a staged trading infrastructure backend.

---

# System Architecture

The system follows a modular trading infrastructure architecture.

Execution pipeline (manual simulated dispatch path):


API Route (e.g. POST /api/v1/copier/dispatch/manual)
→ Execution Engine (execute_order_for_account)
→ Manual Dispatch Service (process_manual_simulated_dispatch_for_account)
→ Sizing (calculate_position_size) + Order Request Validation (validate_order_request_for_execution)
→ build_manual_simulated_order_result / build_manual_dispatch_log_payload
→ Execution Logs (ExecutionLogService.create_log)


For account-based dispatch (stored accounts), the engine delegates to Trade Copier Execution Engine → Exchange Client Service → Exchange Adapter → OrderExecutionResult → Execution Logs.

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
execution_modes.py
order_validation.py

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
execution_engine.py
manual_dispatch_service.py
order_request_validation_service.py
execution_log_service.py

sizing/
position_sizing.py

exchanges/
base.py

tests/
test_execution_engine.py
test_order_request_validation_service.py
test_manual_dispatch_service.py
test_copier_dispatch_routes.py

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

Planned adapters (skeleton implementations present; live not connected):

- Binance
- Bybit
- OKX
- BitGet
- BingX

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

- **simulated** — Implemented and used by manual dispatch. Orders are validated (sizing + order request validation), outcome is decided, and execution is logged; no orders are sent to exchanges.
- **live** — Not implemented yet. Will perform real order placement via exchange APIs when added.

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

**POST /api/v1/copier/dispatch/manual**

Executes dispatch using manually supplied account parameters. Currently runs in **simulated** mode only.

- Accepts: symbol, side, current_price, risk_percent, leverage, list of accounts (account_id, exchange, available_balance, quantity_step, min_quantity, min_notional).
- Per account: sizing → order request validation → decision (build_manual_simulated_order_result) → log payload; then one execution log entry per account and one item in the response.
- Possible per-account statuses in the response:
  - **simulated_dispatched** — Sizing and order request validation passed; simulated execution recorded.
  - **validation_failed** — Sizing validation failed (e.g. balance/limits).
  - **order_request_validation_failed** — Sizing passed but order request validation failed (e.g. side, quantity step, notional consistency).

Order request validation runs before any execution outcome is fixed and affects the final status (validation_failed vs order_request_validation_failed vs simulated_dispatched).

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

**Real Order Request Hardening & Manual Simulated Execution** (current state)

Completed in this phase:

- Order request validation layer (OrderRequestValidationInput/Result, validate_order_request) and integration before adapter.place_market_order in the engine path.
- Validation results attached to execution logs (order_request_status, order_request_errors, execution_mode, etc.).
- Service-layer abstraction for order request validation (validate_order_request_for_execution) and for execution outcome (build_manual_simulated_order_result).
- Log payload built in a dedicated helper (build_manual_dispatch_log_payload); per-account orchestration in manual_dispatch_service (process_manual_simulated_dispatch_for_account) returning a typed dataclass (ManualDispatchAccountProcessingResult).
- Execution modes: enum ExecutionMode (simulated, live); execution_mode passed through the pipeline; manual dispatch uses simulated only.
- Execution Engine abstraction (execute_order_for_account in app/services/execution_engine.py): dispatches to manual simulated flow when mode is simulated; live raises NotImplementedError.
- Manual dispatch route uses execution engine instead of calling orchestration helper directly.

Existing systems (unchanged):

- position sizing engine, multi-account dispatch, exchange abstraction, execution logging, run_id batching, risk engine, side normalization, execution history API.

**Tests**

- **Unit:** execute_order_for_account (simulated returns result, live → NotImplementedError, unsupported → ValueError); build_manual_simulated_order_result (sizing invalid, order request invalid, both valid); process_manual_simulated_dispatch_for_account (typed result, log_payload keys, status).
- **Route:** POST /api/v1/copier/dispatch/manual — success (200, run_id, results, simulated_dispatched); validation failure (200, validation_failed or order_request_validation_failed); log path with mock DB (no real DB write).

**Run tests:** `poetry install` (if not done), then `poetry run pytest tests/ -v`. Route tests use a mock get_db so no database is required.

---

# Next Development Stage

When moving toward live execution (not in scope of current phase):

- Implement live branch in execution engine and exchange adapters (real order placement).
- Wire live_execution_enabled config and guard where appropriate.
- Keep order request validation and execution logging for live path; add execution error handling and real execution logging as needed.

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