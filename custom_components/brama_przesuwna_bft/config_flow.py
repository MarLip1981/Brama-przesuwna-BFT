"""Config flow and options for Brama przesuwna BFT."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    OPTION_OPENING_DIRECTION,
    OPTION_PEDESTRIAN_MODE,
)


def _schema(pedestrian_default: bool, direction_default: str):
    """Build setup/options schema with safe defaults."""
    return vol.Schema(
        {
            vol.Required(
                OPTION_PEDESTRIAN_MODE, default=pedestrian_default
            ): selector.BooleanSelector(),
            vol.Required(
                OPTION_OPENING_DIRECTION, default=direction_default
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": "left", "label": "W lewo"},
                        {"value": "right", "label": "W prawo"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the BFT gate integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for the card options during initial setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(False, "left"),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the integration options flow."""
        return BramaPrzesuwnaBFTOptionsFlow(config_entry)


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage options for the gate card."""

    def __init__(self, config_entry):
        """Keep the entry used to populate the defaults."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Configure pedestrian mode and the viewed opening direction."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        pedestrian = self.config_entry.options.get(
            OPTION_PEDESTRIAN_MODE,
            self.config_entry.data.get(OPTION_PEDESTRIAN_MODE, False),
        )
        direction = self.config_entry.options.get(
            OPTION_OPENING_DIRECTION,
            self.config_entry.data.get(OPTION_OPENING_DIRECTION, "left"),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(pedestrian, direction),
        )
