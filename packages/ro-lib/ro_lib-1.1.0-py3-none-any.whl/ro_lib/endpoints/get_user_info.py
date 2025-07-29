from .._types import *
from ..errors import *
from .base import BaseEndpoint
import logging
import aiohttp

class UserEndpoint(BaseEndpoint):
    async def get_user_info(self, user_id: int) -> User:
        """
        Fetch Roblox user info and populate a User object.

        Args:
            user_id (int): ID of the user (Required)

        Returns:
            User: User object with populated fields
        """
        try:
            info = await self._get_user_basic_info(user_id)
            avatar_url = await self._get_user_avatar(user_id)
            rap_items = await self._get_limited_items(user_id)
            rap_total = self._calculate_total_rap(rap_items)
            counts = await self._get_friend_follower_info(user_id)
            groups = await self._get_user_groups(user_id)

            user = User(
                id=info.get('id', 0),
                name=info.get('name', ''),
                display_name=info.get('displayName', ''),
                description=info.get('description', ''),
                created=info.get('created', ''),
                age=info.get('age', 0),
                is_banned=info.get('isBanned', False),
                friends_count=counts.get('friends', 0),
                followers_count=counts.get('followers', 0),
                following_count=counts.get('followings', 0),
                rap=rap_total if rap_items else None,
                avatar_url=avatar_url,
                groups=groups,
                limited_items=rap_items if rap_items else None
            )
            return user

        except Exception as e:
            logging.error(f"Error getting user: {e}")
            raise BaseError("Error fetching user details")

    async def _get_user_basic_info(self, user_id: int) -> dict:
        url = f"https://users.roblox.com/v1/users/{user_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _get_limited_items(self, user_id: int) -> list:
        asset_types = [2, 8, 41, 42, 43, 44, 45]
        all_items = []
        async with aiohttp.ClientSession() as session:
            for asset_type in asset_types:
                url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?assetType={asset_type}&limit=100"
                async with session.get(url) as res:
                    if res.status == 200:
                        items = (await res.json()).get("data", [])
                        all_items.extend(items)
        return all_items

    def _calculate_total_rap(self, items: list) -> int:
        return sum(item.get("recentAveragePrice", 0) for item in items)

    async def _get_user_avatar(self, user_id: int) -> str:
        url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status == 200:
                    data = await res.json()
                    if data["data"]:
                        return data["data"][0].get("imageUrl")
        return None

    async def _get_friend_follower_info(self, user_id: int) -> dict:
        base = f"https://friends.roblox.com/v1/users/{user_id}"
        counts = {}
        async with aiohttp.ClientSession() as session:
            for category in ["friends", "followers", "followings"]:
                url = f"{base}/{category}/count"
                async with session.get(url) as res:
                    if res.status == 200:
                        counts[category] = (await res.json()).get("count", 0)
        return counts

    async def _get_user_groups(self, user_id: int) -> list:
        url = f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status == 200:
                    return [group["group"]["name"] for group in (await res.json()).get("data", [])]
        return []
    
    async def get_user_id_by_username(self, username: str) -> int | None:
        url = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    users = data.get("data", [])
                    if users:
                        return users[0].get("id")
        return None