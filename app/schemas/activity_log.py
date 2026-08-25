from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)