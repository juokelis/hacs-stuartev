import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aioresponses import aioresponses
from custom_components.stuartev.coordinator import StuartEnergyCoordinator
from custom_components.stuartev.api import StuartEnergyClient


@pytest.mark.asyncio
async def test_coordinator(hass):
    async with async_get_clientsession(hass) as session:
        with aioresponses() as m:
            # Mock the API responses
            m.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AlzaSyBK2HLTRsVtTBcF3uGg-ICYTkpJObsTig",
                   payload={"idToken": "test_token", "refreshToken": "test_refresh_token", "expiresIn": "3600"})
            m.post("https://securetoken.googleapis.com/v1/token?key=AlzaSyBK2HLTRsVtTBcF3uGg-ICYTkpJObsTig", payload={"id_token": "test_access_token", "refresh_token": "test_refresh_token", "expires_in": "3600"})
            m.get("https://api.stuart.energy/api/slink/sites/1/details", payload={
                "energyGeneratedSegments": [{"dateTimeLocal": "2024-02-01T00:00:00", "energyGeneratedKwh": 100}]
            })
            m.get("https://api.stuart.energy/api/slink/sites/1", payload={"name": "Test Site"})

            client = StuartEnergyClient(session, "test@example.com", "password", "1")
            coordinator = StuartEnergyCoordinator(hass, client)
            await coordinator._async_update_data()

            # Assertions
            assert coordinator.data is not None
            assert coordinator.data["energy"]["energyGeneratedSegments"][0]["energyGeneratedKwh"] == 100
            assert coordinator.data["site"]["name"] == "Test Site"
