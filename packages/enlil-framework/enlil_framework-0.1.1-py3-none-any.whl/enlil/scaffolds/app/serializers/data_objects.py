from dataclasses import dataclass
from datetime import datetime

@dataclass
class BaseDataObject:
    """Base data object for internal use."""
    id: int
    created_at: datetime
    updated_at: datetime