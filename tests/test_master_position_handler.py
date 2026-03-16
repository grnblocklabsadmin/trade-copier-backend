"""Unit tests for master position event -> copier orchestration bridge."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.core.master_position import MasterPositionEvent
from app.services.copier_orchestration_service import CopierOrchestrationResult
from app.services.master_position_handler import handle_master_position_event


def test_handle_master_position_event_calls_orchestration_and_returns_result():
    """handle_master_position_event calls execute_copier_from_master_position and returns CopierOrchestrationResult."""
    event = MasterPositionEvent(
        source_exchange="bingx",
        source_account_id=1,
        symbol="BTCUSDT",
        side="buy",
        quantity=Decimal("0.02"),
        entry_price=Decimal("50000"),
        event_type="position_update",
    )
    mock_result = CopierOrchestrationResult(
        run_id="run-1",
        plan_items=[],
        execution_items=[],
        results=[],
    )
    with patch("app.services.master_position_handler.execute_copier_from_master_position", return_value=mock_result) as mock_orch:
        out = handle_master_position_event(
            event=event,
            current_price=Decimal("50000"),
            risk_percent=Decimal("0.01"),
            leverage=Decimal("2"),
            follower_accounts=[],
            follower_positions=None,
            get_account=MagicMock(),
            log_service=MagicMock(),
            run_id=None,
        )
    mock_orch.assert_called_once()
    assert out is mock_result
    assert isinstance(out, CopierOrchestrationResult)


def test_handle_master_position_event_passes_symbol_side_quantity():
    """Symbol, side, quantity from event are passed to orchestration."""
    event = MasterPositionEvent(
        source_exchange="stub",
        source_account_id=None,
        symbol="ETHUSDT",
        side="sell",
        quantity=Decimal("1.5"),
        entry_price=Decimal("3000"),
        event_type="snapshot",
    )
    with patch("app.services.master_position_handler.execute_copier_from_master_position", return_value=MagicMock()) as mock_orch:
        handle_master_position_event(
            event=event,
            current_price=Decimal("3000"),
            risk_percent=Decimal("0.01"),
            leverage=Decimal("2"),
            follower_accounts=[],
            follower_positions=None,
            get_account=MagicMock(),
            log_service=MagicMock(),
            run_id="run-fixed",
        )
    call_kw = mock_orch.call_args.kwargs
    assert call_kw["master_symbol"] == "ETHUSDT"
    assert call_kw["master_side"] == "sell"
    assert call_kw["master_quantity"] == Decimal("1.5")
    assert call_kw["execution_mode"] == "simulated"
    assert call_kw["run_id"] == "run-fixed"
