import aiohttp
import logging
from .endpoints.get_user_info import UserEndpoint
from ._types import *
from .errors import *

class RobloxClient(
        UserEndpoint,
    ):
    def __init__(self):
        ...

    async def _request(self, method: str, target: str, **kwargs):
        """Helper function to make async HTTP requests."""
        url = f"{target}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status() # Will raise an error for bad responses
                if response.status == 204:
                    return None
                if response.status == 404:
                    raise NotFoundError("Not found.")
                return await response.json()