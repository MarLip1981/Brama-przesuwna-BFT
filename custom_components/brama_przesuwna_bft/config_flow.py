"""Config flow and options for Brama przesuwna BFT.

Entity discovery belongs to the Lovelace card editor, following the
AtlasCube pattern. The integration flow only stores integration-level
preferences such as gate direction and notification settings.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DEFAULT_NAME,
    DEFAULT_NOTIFY_TARGET,
    DOMAIN,
    OPTION_NOTIFY_CLOSED,
    OPTION_NOTIFY_OPEN,
    OPTION_NOTIFY_TARGETS,
    OPTION_OPENING_DIRECTION,
    OPTION_PEDESTRIAN_MODE,
)


def _gate_schema(pedestrian_default: bool, direction_default: str):
    """Build the gate-card settings form."""
    return vol.Schema(
        {
            vol.Required(OPTION_PEDESTRIAN_MODE, default=pedestrian_default): selector.BooleanSelector(),
            vol.Required(OPTION_OPENING_DIRECTION, default=direction_default): selector.SelectSelector(
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


def _notification_schema(hass, entry):
    """Build notification settings using notify services available in this HA."""
    services = hass.services.async_services().get("notify", {})
    targets = {DEFAULT_NOTIFY_TARGET}
    targets.update(services)
    options = [{"value": service, "label": f"notify.{service}"} for service in sorted(targets)]
    selected = entry.options.get(
        OPTION_NOTIFY_TARGETS,
        entry.data.get(OPTION_NOTIFY_TARGETS, [DEFAULT_NOTIFY_TARGET]),
    )
    return vol.Schema(
        {
            vol.Required(
                OPTION_NOTIFY_OPEN,
                default=entry.options.get(OPTION_NOTIFY_OPEN, entry.data.get(OPTION_NOTIFY_OPEN, False)),
            ): selector.BooleanSelector(),
            vol.Required(
                OPTION_NOTIFY_CLOSED,
                default=entry.options.get(OPTION_NOTIFY_CLOSED, entry.data.get(OPTION_NOTIFY_CLOSED, False)),
            ): selector.BooleanSelector(),
            vol.Required(OPTION_NOTIFY_TARGETS, default=selected): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the BFT gate integration without duplicating card entity mapping."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry; entity discovery is done by the card editor."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    OPTION_PEDESTRIAN_MODE: user_input[OPTION_PEDESTRIAN_MODE],
                    OPTION_OPENING_DIRECTION: user_input[OPTION_OPENING_DIRECTION],
                    OPTION_NOTIFY_OPEN: False,
                    OPTION_NOTIFY_CLOSED: False,
                    OPTION_NOTIFY_TARGETS: [DEFAULT_NOTIFY_TARGET],
                },
            )
        return self.async_show_form(
            step_id="user",
            data_schema=_gate_schema(False, "right"),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the integration options flow."""
        return BramaPrzesuwnaBFTOptionsFlow()


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage integration-level preferences; card entities stay in Lovelace."""

    async def async_step_init(self, user_input=None):
        """Show the available integration settings."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["gate", "notifications"],
        )

    async def async_step_gate(self, user_input=None):
        """Configure gate direction and optional pedestrian button."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, **user_input},
            )
        pedestrian = self.config_entry.options.get(
            OPTION_PEDESTRIAN_MODE,
            self.config_entry.data.get(OPTION_PEDESTRIAN_MODE, False),
        )
        direction = self.config_entry.options.get(
            OPTION_OPENING_DIRECTION,
            self.config_entry.data.get(OPTION_OPENING_DIRECTION, "right"),
        )
        return self.async_show_form(
            step_id="gate",
            data_schema=_gate_schema(pedestrian, direction),
        )

    async def async_step_notifications(self, user_input=None):
        """Configure notifications without overwriting gate-card options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, **user_input},
            )
        return self.async_show_form(
            step_id="notifications",
            data_schema=_notification_schema(self.hass, self.config_entry),
        )
