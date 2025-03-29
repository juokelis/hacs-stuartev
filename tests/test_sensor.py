import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.stuartev.api import StuartEnergyClient
from custom_components.stuartev.coordinator import StuartEnergyCoordinator
from custom_components.stuartev.sensor import StuartEnergySensor


@pytest.mark.asyncio
async def test_sensor_update(hass):
    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Mock the API responses
            m.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
                   payload={"idToken": "test_token"})
            m.post("https://securetoken.googleapis.com/v1/token", payload={"access_token": "test_access_token"})
            m.get("https://api.stuart.energy/api", payload={"data": {"generated": 100}})

            api = StuartEnergyClient(session, "test@example.com", "password", "1")
            coordinator = StuartEnergyCoordinator(hass, api)
            await coordinator._async_update_data()

            sensor = StuartEnergySensor(coordinator)
            await sensor.async_update()

            # Assertions
            assert sensor.native_value == 100
            assert sensor.name == "Stuart Site Energy Generated"
            assert sensor.native_unit_of_measurement == "kWh"
            assert sensor.device_class == "energy"
