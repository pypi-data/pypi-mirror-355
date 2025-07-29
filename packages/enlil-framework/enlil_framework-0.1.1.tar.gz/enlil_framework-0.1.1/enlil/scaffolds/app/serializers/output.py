from pydantic import BaseModel
from datetime import datetime

class BaseOutput(BaseModel):
    """Base output serializer."""
    id: int
    created_at: datetime
    updated_at: datetime