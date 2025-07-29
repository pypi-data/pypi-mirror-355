from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class BaseQueryParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: Optional[int] = Field(default=100, gt=0)
    order_by: Optional[str] = None
    sort: str = Field(default="asc", pattern="^(asc|desc)$")
    filters: Dict[str, Any] = Field(default_factory=dict)
