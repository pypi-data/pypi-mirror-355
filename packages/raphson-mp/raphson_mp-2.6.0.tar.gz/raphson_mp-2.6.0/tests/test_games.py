from . import T_client


async def test_games(client: T_client):
    async with client.get("/games/guess") as response:
        response.raise_for_status()

    async with client.get("/games/chairs") as response:
        response.raise_for_status()
