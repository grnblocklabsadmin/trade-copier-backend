# Staging Deployment Guide

This document describes how to safely deploy the Trade Copier backend to a **VPS staging environment**.

The project uses **pydantic-settings** (see `app/core/config.py`) to load configuration from environment variables
and a `.env` file in the project root.

Real trading **must NEVER be enabled in staging**.

---

## 1. Staging deployment checklist

1. **Clone the repository**

   ```bash
   git clone <YOUR_REPO_URL>.git
   cd trade-copier
   ```

2. **Install dependencies**

   ```bash
   poetry install
   ```

3. **Create and configure `.env`**

   - Copy the example from this guide (see _Example .env file_ below).
   - Adjust `DATABASE_URL` for your staging PostgreSQL instance.
   - Generate and set a secure `ENCRYPTION_KEY`.
   - Ensure the safety flags are set:

     ```env
     LIVE_EXECUTION_ENABLED=false
     ENABLE_REAL_TRADING=false
     ```

4. **Run database migrations**

   From the project root (where `alembic.ini` lives):

   ```bash
   poetry run alembic upgrade head
   ```

5. **Start the application server**

   On the VPS, run:

   ```bash
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   - After startup, the OpenAPI docs **must** be accessible at:

     - `http://<your-host>:8000/docs`

---

## 2. Required environment variables

Configuration is defined in `app/core/config.py` via `Settings(BaseSettings)`. The following variables are **required** for staging:

- **`DATABASE_URL`** (maps to `database_url: str`)

  Connection string for the PostgreSQL database used by this service.

  Example:

  ```env
  DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/tradecopier_staging
  ```

- **`ENCRYPTION_KEY`** (maps to `encryption_key: str`)

  Secret key used for encryption. Must be a strong, non-guessable value.

  Example (placeholder, generate your own):

  ```env
  ENCRYPTION_KEY=base64_or_random_secret_here
  ```

The following variables are optional but important for staging safety and observability:

- **`APP_ENV`** (`app_env`, default: `"local"`)  
  Recommended for staging:

  ```env
  APP_ENV=staging
  ```

- **`DEBUG`** (`debug`, default: `true`)  
  For staging, debugging should usually be disabled:

  ```env
  DEBUG=false
  ```

- **`API_V1_PREFIX`** (`api_v1_prefix`, default: `"/api/v1"`)  
  Normally left at the default.

- **`LIVE_EXECUTION_ENABLED`** (`live_execution_enabled`, default: `false`)  
  Controls access to live execution routes/guards. For staging, keep it **disabled** unless you explicitly test routing only:

  ```env
  LIVE_EXECUTION_ENABLED=false
  ```

- **`ENABLE_REAL_TRADING`** (`enable_real_trading`, default: `false`)  
  Hard safety gate used in `live_execution_service` for BingX and future live paths.  
  On staging, this **must remain `false`**:

  ```env
  ENABLE_REAL_TRADING=false
  ```

  > **Never** set `ENABLE_REAL_TRADING=true` in staging. Real trading must not be enabled on non-production environments.

---

## 3. Safe defaults for staging

The following defaults are recommended for any staging deployment:

```env
APP_ENV=staging
DEBUG=false
LIVE_EXECUTION_ENABLED=false
ENABLE_REAL_TRADING=false
```

- `LIVE_EXECUTION_ENABLED=false` ensures live execution routes cannot be used inadvertently.
- `ENABLE_REAL_TRADING=false` ensures that even if live routes are hit, real trading is still blocked in `live_execution_service`.

Together, these settings guarantee that **no real orders** can be sent from the staging environment.

---

## 4. Example .env file

Below is a minimal example `.env` suitable for a typical staging VPS (adjust credentials and hostnames as needed):

```env
# Application metadata
APP_NAME=Trade Copier API (staging)
APP_ENV=staging
DEBUG=false
API_V1_PREFIX=/api/v1

# Database (required)
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/tradecopier_staging

# Encryption (required)
ENCRYPTION_KEY=base64_or_random_secret_here

# Safety flags
LIVE_EXECUTION_ENABLED=false
ENABLE_REAL_TRADING=false
```

> Keep this file **out of version control** and store secrets (especially `DATABASE_URL` and `ENCRYPTION_KEY`) securely.

---

## 5. Smoke tests after deployment

Once the application is running on staging, perform these smoke tests to validate basic functionality and safety.

### 5.1 Verify API and docs

1. Open:

   - `http://<your-host>:8000/docs`

2. Ensure:
   - The Swagger UI loads successfully.
   - The copier routes under `/api/v1/copier/...` are visible.

### 5.2 Smoke test: manual dispatch (simulated)

Endpoint: `POST /api/v1/copier/dispatch/manual`

- Use `/docs` or any HTTP client (e.g. `curl`, Postman) to send a request with:
  - `symbol`, `side`, `current_price`, `risk_percent`, `leverage`
  - `accounts`: a list of test accounts (see schema `ManualCopierDispatchAccount` in `app/schemas/copier.py`).

Expected behavior:

- Response HTTP status is `200`.
- Response body contains:
  - `run_id` (non-null).
  - `results`: a non-empty list with one item per account.
  - Each `dispatch_status` is in the simulated execution set:

    ```text
    simulated_dispatched
    validation_failed
    order_request_validation_failed
    ```

- No real orders are sent to any exchange (this path operates in **simulated** mode).

### 5.3 Smoke test: copier dry-run plan dispatch

Endpoint: `POST /api/v1/copier/plan/dispatch`

- Send a payload with:

  - `symbol`, `side`, `master_quantity`, `current_price`, `risk_percent`, `leverage`
  - `follower_accounts`: list of follower accounts (same shape as manual dispatch accounts).
  - `follower_positions`: either empty or a small map of `account_id` → position quantity.

Expected behavior:

- Response HTTP status is `200`.
- Response body contains:
  - `run_id` (non-null).
  - `plan_items`: list with one item per follower, each having:
    - `action` in `{ "open", "hold", "increase", "reduce" }`.
  - `execution_items_count` equal to the number of non-`hold` plan items.
  - `results`: list of simulated execution results for non-`hold` accounts.

Again, **no real trading** happens — this is a dry-run / simulated orchestration path.

### 5.4 Verify that real trading is blocked

Even if you experiment with live-related routes in the future:

1. Confirm your staging `.env` has:

   ```env
   LIVE_EXECUTION_ENABLED=false
   ENABLE_REAL_TRADING=false
   ```

2. Any attempt to trigger a BingX live execution path will:
   - Read settings via `get_settings()` from `app/core/config.py`.
   - See `enable_real_trading=False`.
   - Raise an error instead of sending a real order.

This guarantees that **real trading must NEVER be enabled in staging**, and any misconfiguration should surface as a clear error rather than silent live trading.

