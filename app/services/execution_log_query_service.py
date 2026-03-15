from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution_log import ExecutionLog


class ExecutionLogQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_logs(self, limit: int = 50) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .order_by(ExecutionLog.id.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_logs_by_run_id(self, run_id: str) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.run_id == run_id)
            .order_by(ExecutionLog.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())