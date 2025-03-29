from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .auth import StuartAuth
from .api import StuartEnergyClient
from .coordinator import StuartEnergyCoordinator
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = entry.data
    options = entry.options

    email = data["email"]
    password = data["password"]
    site_id = data["site_id"]
    history_days = options.get("history_days") if options else data.get("history_days", 30)
    scan_interval = options.get("scan_interval") if options else data.get("scan_interval", 3)

    session = async_get_clientsession(hass)
    client = StuartEnergyClient(session, email, password, site_id)
    _coordinator = StuartEnergyCoordinator(hass, client, scan_interval=scan_interval)

    # Import historical data on initial setup
    await _coordinator.import_historical_data(history_days)

    await _coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": _coordinator,
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
