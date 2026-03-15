import json
from sqlalchemy.orm import Session

from app.models.execution_log import ExecutionLog


class ExecutionLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(
        self,
        event_type: str,
        symbol: str,
        side: str,
        account_id: int,
        exchange: str,
        status: str,
        message: str | None = None,
        payload: dict | None = None,
        run_id: str | None = None,
    ) -> ExecutionLog:
        payload_json = json.dumps(payload, ensure_ascii=False) if payload is not None else None

        log = ExecutionLog(
            run_id=run_id,
            event_type=event_type,
            symbol=symbol,
            side=side,
            account_id=account_id,
            exchange=exchange,
            status=status,
            message=message,
            payload_json=payload_json,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log