"""
Route-level tests for POST /api/v1/copier/dispatch/manual (dispatch_manual_copier_plan).
Uses TestClient + mock get_db so no real DB is required; log path is exercised without persistence.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app


def _mock_db():
    return MagicMock()


@pytest.fixture
def client_with_mock_db():
    def override_get_db():
        yield _mock_db()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


def _valid_payload():
    return {
        "symbol": "BTCUSDT",
        "side": "buy",
        "current_price": "50000",
        "risk_percent": "0.01",
        "leverage": "2",
        "accounts": [
            {
                "account_id": 1,
                "exchange": "binance",
                "available_balance": "1000",
                "quantity_step": "0.001",
                "min_quantity": "0.001",
                "min_notional": "5",
            }
        ],
    }


def _payload_with_invalid_sizing():
    """One account with zero balance so sizing validation fails."""
    return {
        "symbol": "BTCUSDT",
        "side": "buy",
        "current_price": "50000",
        "risk_percent": "0.01",
        "leverage": "2",
        "accounts": [
            {
                "account_id": 1,
                "exchange": "binance",
                "available_balance": "0",
                "quantity_step": "0.001",
                "min_quantity": "0.001",
                "min_notional": "5",
            }
        ],
    }


def test_dispatch_manual_success_returns_200_run_id_and_results(client_with_mock_db):
    response = client_with_mock_db.post("/api/v1/copier/dispatch/manual", json=_valid_payload())
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1
    assert data["results"][0]["dispatch_status"] == "simulated_dispatched"


def test_dispatch_manual_validation_failure_returns_200_and_failed_status(client_with_mock_db):
    response = client_with_mock_db.post(
        "/api/v1/copier/dispatch/manual", json=_payload_with_invalid_sizing()
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["dispatch_status"] in (
        "validation_failed",
        "order_request_validation_failed",
    )
    assert data["results"][0]["dispatched"] is False


def test_dispatch_manual_log_creation_path_succeeds_with_mock_db(client_with_mock_db):
    """With get_db overridden to a mock, create_log is called without real DB; request still succeeds."""
    response = client_with_mock_db.post("/api/v1/copier/dispatch/manual", json=_valid_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] is not None
    assert len(data["results"]) == 1


# --- POST /api/v1/copier/plan/dispatch (dry-run copier) ---


def _plan_dispatch_payload(include_positions=False):
    """Payload for plan/dispatch: one follower. If not include_positions -> no position -> open."""
    payload = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "master_quantity": "10",
        "current_price": "50000",
        "risk_percent": "0.01",
        "leverage": "2",
        "follower_accounts": [
            {
                "account_id": 1,
                "exchange": "bingx",
                "available_balance": "1000",
                "quantity_step": "0.001",
                "min_quantity": "0.001",
                "min_notional": "5",
            }
        ],
    }
    if include_positions:
        payload["follower_positions"] = {"1": "0"}
    return payload


def test_plan_dispatch_follower_without_position_returns_200_run_id_plan_open_results(client_with_mock_db):
    """POST /copier/plan/dispatch: follower without position -> plan has action open, 200, run_id, non-empty results."""
    payload = _plan_dispatch_payload(include_positions=False)
    response = client_with_mock_db.post("/api/v1/copier/plan/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert "plan_items" in data
    assert len(data["plan_items"]) == 1
    assert data["plan_items"][0]["action"] == "open"
    assert "execution_items_count" in data
    assert data["execution_items_count"] == 1
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1


def test_plan_dispatch_mixed_positions_hold_and_increase(client_with_mock_db):
    """POST /copier/plan/dispatch: two followers — one hold (qty==master), one increase (qty<master); execution only for increase."""
    payload = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "master_quantity": "0.020",
        "current_price": "50000",
        "risk_percent": "0.01",
        "leverage": "2",
        "follower_accounts": [
            {
                "account_id": 1,
                "exchange": "bingx",
                "available_balance": "1000",
                "quantity_step": "0.001",
                "min_quantity": "0.001",
                "min_notional": "5",
            },
            {
                "account_id": 2,
                "exchange": "stub",
                "available_balance": "1000",
                "quantity_step": "0.001",
                "min_quantity": "0.001",
                "min_notional": "5",
            },
        ],
        "follower_positions": {"1": "0.020", "2": "0.010"},
    }
    response = client_with_mock_db.post("/api/v1/copier/plan/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None
    assert len(data["plan_items"]) == 2
    actions = [p["action"] for p in data["plan_items"]]
    assert "hold" in actions
    assert "increase" in actions
    assert data["execution_items_count"] == 1
    assert len(data["results"]) == 1
