from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.execution_log import ExecutionLogRead
from app.services.execution_log_query_service import ExecutionLogQueryService

router = APIRouter(prefix="/execution-logs", tags=["execution-logs"])


@router.get("", response_model=list[ExecutionLogRead])
def get_execution_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ExecutionLogRead]:
    service = ExecutionLogQueryService(db)
    logs = service.get_latest_logs(limit=limit)
    return [ExecutionLogRead.model_validate(log) for log in logs]


@router.get("/run/{run_id}", response_model=list[ExecutionLogRead])
def get_execution_logs_by_run_id(
    run_id: str,
    db: Session = Depends(get_db),
) -> list[ExecutionLogRead]:
    service = ExecutionLogQueryService(db)
    logs = service.get_logs_by_run_id(run_id=run_id)
    return [ExecutionLogRead.model_validate(log) for log in logs]