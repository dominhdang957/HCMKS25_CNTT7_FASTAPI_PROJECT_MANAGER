from pydantic import BaseModel,ConfigDict
from typing import Any
from datetime import datetime,timezone
from fastapi.requests import Request

class APIResponse(BaseModel):
    success: bool = True
    statusCode: int
    message: str = "Thành công"
    data: Any = None
    timestamp: datetime
    path: str
    model_config = ConfigDict(populate_by_name=True)

def api_response(status_code:int,message:str,data:Any,request:Request):
    return APIResponse(
        success=True,
        statusCode=status_code,
        message=message,
        data=data,
        timestamp=datetime.now(timezone.utc),
        path=request.url.path
    )