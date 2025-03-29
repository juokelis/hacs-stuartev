import pytest
import aiohttp
from aioresponses import aioresponses
from custom_components.stuartev.sensor import StuartEnergySensor
from custom_components.stuartev.api import StuartEnergyClient


@pytest.mark.asyncio
async def test_sensor_update():
    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Mock the API responses
            m.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
                   payload={"idToken": "test_token"})
            m.post("https://securetoken.googleapis.com/v1/token", payload={"access_token": "test_access_token"})
            m.get("https://api.stuart.energy/api", payload={"data": {"generated": 100}})

            api = StuartEnergyClient(session, "test@example.com", "password", "1")
            sensor = StuartEnergySensor(api)
            await sensor.async_update()

            # Assertions
            assert sensor.state == 100
            assert sensor.name == "Stuart Energy Sensor"
            assert sensor.unit_of_measurement == "kWh"
            assert sensor.device_class == "energy"