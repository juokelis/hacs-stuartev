"""
Config flow for Stuart Energy integration.

This module defines the configuration flow for setting up the Stuart Energy integration
in Home Assistant, including user input handling and options flow.
"""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from . import DAYS_DEFAULT, DAYS_MAX
from .api import (
    StuartEnergyApiClientAuthenticationError,
    StuartEnergyApiClientCommunicationError,
)
from .auth import StuartAuth
from .const import DOMAIN, LOGGER, SCAN_INTERVAL_DEFAULT, SCAN_INTERVAL_MAX


class StuartEVConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stuart Energy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handle the initial step of the config flow.

        :param user_input: User input from the form
        :return: Config flow result
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input["email"].strip().lower()
            password = user_input["password"]
            site_id = user_input["site_id"]
            api_key = user_input[CONF_API_KEY]
            history_days = user_input.get("history_days", DAYS_DEFAULT)
            scan_interval = user_input.get("scan_interval", SCAN_INTERVAL_DEFAULT)

            if not (1 <= history_days <= DAYS_MAX):
                errors["history_days"] = "invalid_range"
            if not (1 <= scan_interval <= SCAN_INTERVAL_MAX):
                errors["scan_interval"] = "invalid_range"

            if not errors:
                auth = StuartAuth(self.hass, email, password, api_key)

                try:
                    token = await auth.authenticate()
                    if token:
                        return self.async_create_entry(
                            title="Stuart Energy",
                            data={
                                "email": email,
                                "password": password,
                                "site_id": site_id,
                                CONF_API_KEY: api_key,
                                "history_days": history_days,
                                "scan_interval": scan_interval,
                            },
                        )
                    errors["base"] = "invalid_auth"
                except StuartEnergyApiClientAuthenticationError:
                    errors["base"] = "invalid_auth"
                except StuartEnergyApiClientCommunicationError:
                    errors["base"] = "cannot_connect"
                except (ValueError, RuntimeError) as e:
                    errors["base"] = "unknown"
                    LOGGER.error("Unexpected exception: %s", e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str,
                    vol.Required("site_id"): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional("history_days", default=DAYS_DEFAULT): int,
                    vol.Optional("scan_interval", default=SCAN_INTERVAL_DEFAULT): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """
        Get the options flow for this handler.

        :param config_entry: Config entry
        :return: Options flow instance
        """
        return StuartEVOptionsFlow(config_entry)


class StuartEVOptionsFlow(OptionsFlow):
    """Handle options flow for Stuart Energy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """
        Initialize the options flow.

        :param config_entry: Config entry
        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handle the initial step of the options flow.

        :param user_input: User input from the form
        :return: Form or entry creation result
        """
        if user_input is not None:
            old_days = self.config_entry.options.get("history_days", DAYS_DEFAULT)
            new_days = user_input.get("history_days", DAYS_DEFAULT)
            result: ConfigFlowResult = self.async_create_entry(
                title="", data=user_input
            )

            if new_days != old_days:

                async def trigger_import() -> None:
                    """Trigger import of historical data after option change."""
                    coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][
                        "coordinator"
                    ]
                    await coordinator.import_historical_data(new_days)

                self.hass.async_create_task(trigger_import())

            return result

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("scan_interval", default=SCAN_INTERVAL_DEFAULT): int,
                    vol.Optional("history_days", default=DAYS_DEFAULT): int,
                }
            ),
        )
