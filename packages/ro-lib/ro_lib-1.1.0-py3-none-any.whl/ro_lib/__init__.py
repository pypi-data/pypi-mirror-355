from typing import TYPE_CHECKING, List, Union, Dict, Optional, Any

# Import actual types for runtime
from ._types import *
from .api import RobloxClient as _BaseClient

# Create unified type exports
RobloxType = Union[
    User
]

class RobloxClient(_BaseClient):
    """
    FULL DOCUMENTATION AVAILABLE AT
    """
    if TYPE_CHECKING:
        
        # Internal method
        async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]: ...

# Export everything needed
__all__ = [
    "RobloxClient",
    "User"
]