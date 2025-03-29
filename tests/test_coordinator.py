import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aioresponses import aioresponses
from custom_components.stuartev.coordinator import StuartEnergyUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator(hass):
    entry = {"email": "test@example.com", "password": "password", "site_id": "1"}
    async with async_get_clientsession(hass) as session:
        with aioresponses() as m:
            # Mock the API responses
            m.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
                   payload={"idToken": "test_token"})
            m.post("https://securetoken.googleapis.com/v1/token", payload={"access_token": "test_access_token"})
            m.get("https://api.stuart.energy/api", payload={"data": {"generated": 100}})

            coordinator = StuartEnergyUpdateCoordinator(hass, entry)
            await coordinator._async_update_data()

            # Assertions
            assert coordinator.data is not None
            assert coordinator.data["generated"] == 100