from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    display_name: str
    description: str
    created: str
    age: int
    is_banned: bool
    friends_count: int
    followers_count: int
    following_count: int
    rap: Optional[int]
    avatar_url: Optional[str] = None
    groups: Optional[list[str]] = None
    limited_items: Optional[list[dict]] = None