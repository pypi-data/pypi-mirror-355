import aiohttp
from .exceptions import EOLTrackerAPIError

class EOLClient:
    def __init__(self, session):
        self._session = session

    async def fetch_release_data(self, uri: str) -> dict:
        try:
            async with self._session.get(uri) as release_resp:
                if release_resp.status != 200:
                    raise EOLTrackerAPIError(
                        f"Failed to fetch release data from {uri}")
                return (await release_resp.json()).get("result", {})
        except aiohttp.ClientError as e:
            raise EOLTrackerAPIError(f"HTTP error while fetching release data: {e}")

    async def fetch_product_data(self, uri: str) -> dict:
        base_uri = "/".join(uri.strip("/").split("/")[:-2])
        try:
            async with self._session.get(base_uri) as product_resp:
                if product_resp.status != 200:
                    raise EOLTrackerAPIError(
                        f"Failed to fetch product data from {base_uri}")
                return (await product_resp.json()).get("result", {})
        except aiohttp.ClientError as e:
            raise EOLTrackerAPIError(f"HTTP error while fetching product data: {e}")

    async def fetch_all(self, uri: str) -> dict:
        release_data = await self.fetch_release_data(uri)
        product_data = await self.fetch_product_data(uri)
        return {
            "release": release_data,
            "product": product_data
        }

    async def close(self):
        await self._session.close()
