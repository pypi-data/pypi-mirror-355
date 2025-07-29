from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ErrorDetail(BaseModel):
    loc: Optional[List[str]]
    msg: str
    type: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    status_code: int
    error_id: str = Field(default_factory=lambda: str(uuid4()))
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error_type: str
