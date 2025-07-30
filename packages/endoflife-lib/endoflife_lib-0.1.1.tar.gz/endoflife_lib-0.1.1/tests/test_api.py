import pytest
from aioresponses import aioresponses
from aiohttp import ClientSession
from eoltracker.api import EOLClient
from eoltracker.exceptions import EOLTrackerAPIError

RELEASE_URL = "https://endoflife.date/api/v1/products/iPad/releases/11"
PRODUCT_URL = "https://endoflife.date/api/v1/products/iPad"

release_payload = {
    "result": {
        "label": "iPadOS 11",
        "isLts": False,
        "releaseDate": "2017-09-19"
    }
}

product_payload = {
    "result": {
        "label": "iPad",
        "links": {
            "html": "https://endoflife.date/ipad",
            "icon": "https://example.com/icon.png"
        }
    }
}

@pytest.mark.asyncio
async def test_fetch_release_data_success():
    with aioresponses() as m:
        m.get(RELEASE_URL, payload=release_payload)
        async with ClientSession() as session:
            client = EOLClient(session)
            data = await client.fetch_release_data(RELEASE_URL)
            assert data["label"] == "iPadOS 11"

@pytest.mark.asyncio
async def test_fetch_product_data_success():
    with aioresponses() as m:
        m.get(PRODUCT_URL, payload=product_payload)
        async with ClientSession() as session:
            client = EOLClient(session)
            data = await client.fetch_product_data(RELEASE_URL)
            assert data["label"] == "iPad"

@pytest.mark.asyncio
async def test_fetch_all_success():
    with aioresponses() as m:
        m.get(RELEASE_URL, payload=release_payload)
        m.get(PRODUCT_URL, payload=product_payload)
        async with ClientSession() as session:
            client = EOLClient(session)
            data = await client.fetch_all(RELEASE_URL)
            assert "release" in data and "product" in data

@pytest.mark.asyncio
async def test_fetch_release_data_error():
    with aioresponses() as m:
        m.get(RELEASE_URL, status=404)
        async with ClientSession() as session:
            client = EOLClient(session)
            with pytest.raises(EOLTrackerAPIError):
                await client.fetch_release_data(RELEASE_URL)

@pytest.mark.asyncio
async def test_fetch_product_data_error():
    with aioresponses() as m:
        m.get(PRODUCT_URL, status=500)
        async with ClientSession() as session:
            client = EOLClient(session)
            with pytest.raises(EOLTrackerAPIError):
                await client.fetch_product_data(RELEASE_URL)
