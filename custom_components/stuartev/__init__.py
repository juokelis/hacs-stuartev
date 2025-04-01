"""
Custom integration to integrate stuart.energy with Home Assistant.

This module initializes the Stuart Energy integration, setting up the necessary
components and handling the configuration entries.

For more details about this integration, please refer to
https://github.com/juokelis/hacs-stuartev
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import StuartEnergyApiClientCommunicationError
from .const import DAYS_DEFAULT, DAYS_MAX, DOMAIN, LOGGER
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

    # Guard clause to prevent issues if config is incomplete
    required_keys = ("email", "password", "site_id", "api_key")
    if not all(k in data and data[k] for k in required_keys):
        return False

    history_days = (
        options.get("history_days")
        if options
        else data.get("history_days", DAYS_DEFAULT)
    )
    if not (1 <= history_days <= DAYS_MAX):
        history_days = DAYS_DEFAULT

    _coordinator = StuartEnergyCoordinator(hass, entry)

    try:
        await _coordinator.initialize_site_info()
        await _coordinator.import_historical_data(history_days)
        await _coordinator.async_config_entry_first_refresh()
    except StuartEnergyApiClientCommunicationError as err:
        LOGGER.exception(
            "StuartEV setup failed due to API communication error: %s", err
        )
        return False
    except ValueError as err:
        LOGGER.exception("StuartEV setup failed due to invalid data: %s", err)
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": _coordinator,
        "client": _coordinator.api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

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
