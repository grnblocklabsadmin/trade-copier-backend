from datetime import datetime

from pydantic import BaseModel


class ExecutionLogRead(BaseModel):
    id: int
    run_id: str | None
    event_type: str
    symbol: str
    side: str
    account_id: int
    exchange: str
    status: str
    message: str | None
    payload_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}