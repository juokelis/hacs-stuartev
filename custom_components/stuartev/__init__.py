"""
Custom integration to integrate stuart.energy with Home Assistant.

This module initializes the Stuart Energy integration, setting up the necessary
components and handling the configuration entries.

For more details about this integration, please refer to
https://github.com/juokelis/hacs-stuartev
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DAYS_DEFAULT, DAYS_MAX, DOMAIN
from .coordinator import StuartEnergyCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Stuart Energy integration from a config entry.

    :param hass: Home Assistant instance
    :param entry: Config entry with user data
    :return: True if setup was successful, False otherwise
    """
    data = entry.data
    options = entry.options

    history_days = (
        options.get("history_days")
        if options
        else data.get("history_days", DAYS_DEFAULT)
    )
    if not (1 <= history_days <= DAYS_MAX):
        history_days = DAYS_DEFAULT

    _coordinator = StuartEnergyCoordinator(hass, entry)

    # Import historical data on initial setup
    await _coordinator.import_historical_data(history_days)

    await _coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": _coordinator,
        "client": _coordinator.api,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.

    :param hass: Home Assistant instance
    :param entry: Config entry to unload
    :return: True if unload was successful, False otherwise
    """
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
