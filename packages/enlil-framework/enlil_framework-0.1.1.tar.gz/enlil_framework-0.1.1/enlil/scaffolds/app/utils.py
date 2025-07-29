from typing import Any, Dict

def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary."""
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return {}