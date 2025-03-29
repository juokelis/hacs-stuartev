import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from aiohttp import ClientSession
from .const import DOMAIN
from .auth import StuartAuth

class StuartEVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            email = user_input["email"]
            password = user_input["password"]
            site_id = user_input["site_id"]

            session = ClientSession()
            auth = StuartAuth(session, email, password)

            try:
                token = await auth.authenticate()
                await session.close()
                if token:
                    return self.async_create_entry(title="Stuart Energy", data=user_input)
                else:
                    errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
                await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Required("site_id"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return StuartEVOptionsFlow(config_entry)


class StuartEVOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("scan_interval", default="1h"): str,
            })
        )
