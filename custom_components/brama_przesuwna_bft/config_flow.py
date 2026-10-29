"""Config flow and options for Brama przesuwna BFT."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DEFAULT_NAME, DOMAIN, OPTION_PEDESTRIAN_MODE


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the BFT gate integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry with pedestrian mode disabled by default."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title=DEFAULT_NAME, data={})

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the integration options flow."""
        return BramaPrzesuwnaBFTOptionsFlow()


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage options for the gate card."""

    async def async_step_init(self, user_input=None):
        """Configure whether the pedestrian-gate action is available."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        OPTION_PEDESTRIAN_MODE,
                        default=self.config_entry.options.get(OPTION_PEDESTRIAN_MODE, False),
                    ): selector.BooleanSelector(),
                }
            ),
        )
