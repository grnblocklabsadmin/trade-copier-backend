"""
End-to-end service-layer integration test for copier pipeline.
MasterPositionEvent -> handle_master_position_event -> CopierOrchestrationResult.
Uses real planning, execution preparation, runner and execution_engine; only log_service mocked.
"""
from decimal import Decimal
from unittest.mock import MagicMock

from app.core.master_position import MasterPositionEvent
from app.schemas.copier import ManualCopierDispatchAccount
from app.services.copier_orchestration_service import CopierOrchestrationResult
from app.services.master_position_handler import handle_master_position_event

SIMULATED_DISPATCH_STATUSES = (
    "simulated_dispatched",
    "validation_failed",
    "order_request_validation_failed",
)


def test_master_position_event_to_orchestration_result_e2e():
    """
    MasterPositionEvent -> handle_master_position_event -> full service chain -> CopierOrchestrationResult.
    One follower, no position -> plan action open, one execution item, one result; log_service.create_log called once.
    """
    event = MasterPositionEvent(
        source_exchange="bingx",
        source_account_id=100,
        symbol="BTCUSDT",
        side="buy",
        quantity=Decimal("0.020"),
        entry_price=Decimal("50000"),
        event_type="position_opened",
    )
    follower_accounts = [
        ManualCopierDispatchAccount(
            account_id=1,
            exchange="bingx",
            available_balance=Decimal("1000"),
            quantity_step=Decimal("0.001"),
            min_quantity=Decimal("0.001"),
            min_notional=Decimal("5"),
        ),
    ]
    accounts_by_id = {a.account_id: a for a in follower_accounts}

    def get_account(account_id: int) -> ManualCopierDispatchAccount:
        if account_id not in accounts_by_id:
            raise ValueError(f"Account {account_id} not found.")
        return accounts_by_id[account_id]

    log_service = MagicMock()
    log_service.create_log = MagicMock()

    result = handle_master_position_event(
        event=event,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        follower_accounts=follower_accounts,
        follower_positions=None,
        get_account=get_account,
        log_service=log_service,
        run_id=None,
    )

    assert isinstance(result, CopierOrchestrationResult)
    assert result.run_id is not None
    assert len(result.run_id) > 0
    assert len(result.plan_items) == 1
    assert result.plan_items[0].action == "open"
    assert len(result.execution_items) == 1
    assert len(result.results) == 1
    assert result.results[0].dispatch_status in SIMULATED_DISPATCH_STATUSES
    assert log_service.create_log.call_count == 1
