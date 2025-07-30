from typing import Any, Dict, Optional

from pydantic import BaseModel


class RequestData(BaseModel):
    url: str
    payload: Optional[Dict[str, Any]]
    headers: Dict[str, Any]
    correlation_id: str
