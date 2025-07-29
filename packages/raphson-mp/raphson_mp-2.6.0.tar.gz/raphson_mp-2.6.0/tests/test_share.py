from aiohttp import web

from tests import T_client, get_csrf


async def test_share(client: T_client, track: str):
    async with client.post(
        "/share/create", json={"track": track, "csrf": await get_csrf(client)}, raise_for_status=True
    ) as response:
        response.raise_for_status()
        share_code = (await response.json())["code"]

    async with client.get("/share/" + share_code, allow_redirects=False) as response:
        assert response.status == web.HTTPSeeOther.status_code
        track_page = response.headers["Location"]

    async with client.get(track_page, raise_for_status=True) as response:
        pass

    async with client.get(f"{track_page}/cover", raise_for_status=True) as response:
        pass

    async with client.get(f"{track_page}/audio", raise_for_status=True) as response:
        pass

    async with client.get(f"{track_page}/download/mp3", raise_for_status=True) as response:
        pass

    async with client.get(f"{track_page}/download/original", raise_for_status=True) as response:
        pass
