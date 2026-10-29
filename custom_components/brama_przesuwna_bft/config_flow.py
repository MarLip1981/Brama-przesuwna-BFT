"""Config flow for the BFT sliding gate project."""

import voluptuous as vol
from homeassistant import config_entries

from .const import DEFAULT_NAME, DOMAIN


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the project integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the initial project entry."""
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
