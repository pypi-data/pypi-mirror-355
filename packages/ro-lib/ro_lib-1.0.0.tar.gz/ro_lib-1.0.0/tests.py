import asyncio
from ro_lib import RobloxClient

async def main():
    client = RobloxClient()
    try:
        user = await client._get_user_avatar(24181857)
        print(user)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())