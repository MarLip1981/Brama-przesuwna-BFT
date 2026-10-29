"""Config flow for the BFT sliding gate project."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DEFAULT_NAME, DOMAIN


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the project integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for a display name and create one project entry."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={"name": user_input["name"]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("name", default=DEFAULT_NAME): str}
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """No options flow yet; project configurator is planned for a later stage."""
        return BramaPrzesuwnaBFTOptionsFlow(config_entry)


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlow):
    """Placeholder options flow for future configuration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """No configurable options are exposed in this initial HACS package."""
        return self.async_abort(reason="no_options")
