from pydantic import BaseModel, Field
from typing import Dict, Any


class ContextRequest(BaseModel):
    name: str = Field(..., alias="context_name")
    version: str = Field(..., alias="context_version")
    body: Dict[str, Any]
