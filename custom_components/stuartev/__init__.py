"""
Custom integration to integrate stuart.energy with Home Assistant.

This module initializes the Stuart Energy integration, setting up the necessary
components and handling the configuration entries.

For more details about this integration, please refer to
https://github.com/juokelis/hacs-stuartev
"""

from functools import partial
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .api import StuartEnergyApiClientCommunicationError
from .const import CONF_API_KEY, DAYS_DEFAULT, DAYS_MAX, DOMAIN, LOGGER
from .coordinator import StuartEnergyCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall


SERVICE_IMPORT_HISTORY = "import_history"
SERVICE_SCHEMA_IMPORT_HISTORY = vol.Schema(
    {
        vol.Optional("days", default=DAYS_DEFAULT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=DAYS_MAX)
        )
    }
)


async def _async_handle_import_history(hass: HomeAssistant, call: ServiceCall) -> None:
    """Re-import recent historical statistics for all loaded Stuart entries."""
    days = call.data["days"]
    domain_data: dict[str, dict[str, Any]] = hass.data.get(DOMAIN, {})

    if not domain_data:
        LOGGER.warning("Import requested but no Stuart Energy entries are loaded.")
        return

    for entry_id, entry_data in domain_data.items():
        coordinator: StuartEnergyCoordinator = entry_data["coordinator"]
        LOGGER.info(
            "Re-importing %d days of Stuart Energy history for entry %s",
            days,
            entry_id,
        )
        await coordinator.import_historical_data(days)


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
    required_keys = (CONF_EMAIL, CONF_PASSWORD, CONF_API_KEY, "site_id")
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

    if not hass.services.has_service(DOMAIN, SERVICE_IMPORT_HISTORY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_IMPORT_HISTORY,
            partial(_async_handle_import_history, hass),
            schema=SERVICE_SCHEMA_IMPORT_HISTORY,
        )

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
    if not hass.data[DOMAIN] and hass.services.has_service(
        DOMAIN, SERVICE_IMPORT_HISTORY
    ):
        hass.services.async_remove(DOMAIN, SERVICE_IMPORT_HISTORY)
    return True
