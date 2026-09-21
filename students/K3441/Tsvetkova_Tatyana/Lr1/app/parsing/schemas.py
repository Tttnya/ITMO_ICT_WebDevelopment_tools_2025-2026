from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ParseRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"url": "https://www.python.org"}}
    )

    url: str


class ParseResult(BaseModel):
    id: int
    url: str
    title: str
    approach: str
    created_at: datetime


class ParseTaskAccepted(BaseModel):
    task_id: str
    status: str


class ParseTaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[ParseResult] = None
