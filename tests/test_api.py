import pytest
import aiohttp
from aioresponses import aioresponses
from custom_components.stuartev.api import StuartEnergyClient


@pytest.mark.asyncio
async def test_fetch_energy_data():
    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Mock the API response
            m.get("https://api.stuart.energy/api", payload={"data": {"generated": 100}})

            api = StuartEnergyClient(session, "test@example.com", "password", "1")
            data = await api.async_get_energy_data("2024-02-01T00:00:00", "2024-02-01T23:59:59")

            # Assertions
            assert data is not None
            assert data["generated"] == 100