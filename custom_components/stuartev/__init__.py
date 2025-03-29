from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .auth import StuartAuth
from .api import StuartEnergyClient
from .coordinator import StuartEnergyCoordinator
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = entry.data
    email = data["email"]
    password = data["password"]
    site_id = data["site_id"]

    session = hass.helpers.aiohttp_client.async_get_clientsession()
    client = StuartEnergyClient(session, email, password, site_id)
    coordinator = StuartEnergyCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
