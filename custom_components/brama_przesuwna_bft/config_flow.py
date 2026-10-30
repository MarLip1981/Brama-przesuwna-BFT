"""Config flow and options for Brama przesuwna BFT."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .discovery import discover_esphome_gate_nodes

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


def _notification_schema(hass, entry):
    """Build notification settings using notify services available in this HA."""
    services = hass.services.async_services().get("notify", {})
    targets = {DEFAULT_NOTIFY_TARGET}
    targets.update(services)
    options = [
        {"value": service, "label": f"notify.{service}"}
        for service in sorted(targets)
    ]
    selected = entry.options.get(
        OPTION_NOTIFY_TARGETS,
        entry.data.get(OPTION_NOTIFY_TARGETS, [DEFAULT_NOTIFY_TARGET]),
    )
    return vol.Schema(
        {
            vol.Required(
                OPTION_NOTIFY_OPEN,
                default=entry.options.get(
                    OPTION_NOTIFY_OPEN, entry.data.get(OPTION_NOTIFY_OPEN, False)
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                OPTION_NOTIFY_CLOSED,
                default=entry.options.get(
                    OPTION_NOTIFY_CLOSED, entry.data.get(OPTION_NOTIFY_CLOSED, False)
                ),
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
    """Set up the BFT gate integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for the card options during initial setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="user",
                data_schema=_gate_schema(False, "left"),
                errors={"base": "no_matching_esphome_device"},
            )

        if user_input is not None:
            selected_id = user_input.pop("esphome_device", nodes[0]["device_id"])
            selected = next((node for node in nodes if node["device_id"] == selected_id), None)
            if selected is None:
                return self.async_abort(reason="device_not_found")
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    **user_input,
                    "esphome_device_id": selected["device_id"],
                    "esphome_node_id": selected["node_id"],
                    "esphome_entities": selected["entities"],
                    "esphome_device_name": selected["name"],
                    OPTION_NOTIFY_OPEN: False,
                    OPTION_NOTIFY_CLOSED: False,
                    OPTION_NOTIFY_TARGETS: [DEFAULT_NOTIFY_TARGET],
                },
            )

        schema = dict(_gate_schema(False, "left").schema)
        schema[vol.Required("esphome_device", default=nodes[0]["device_id"])] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": node["device_id"], "label": node["name"]}
                    for node in nodes
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the integration options flow."""
        return BramaPrzesuwnaBFTOptionsFlow()


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage gate-card settings and notifications in separate sections."""

    async def async_step_init(self, user_input=None):
        """Show separate settings sections."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["device", "gate", "notifications"],
        )

    async def async_step_device(self, user_input=None):
        """Select the physical controller and correct its entity-role mapping."""
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )

        if user_input is not None:
            selected_id = user_input.get("esphome_device", nodes[0]["device_id"])
            selected = next((node for node in nodes if node["device_id"] == selected_id), None)
            if selected is None:
                return self.async_abort(reason="device_not_found")
            manual_entities = {
                role: user_input.get(role) or selected["entities"].get(role, "")
                for role in ("status", "position", "main_button", "pedestrian_button")
            }
            values = {
                "esphome_device_id": selected["device_id"],
                "esphome_node_id": selected["node_id"],
                "esphome_device_name": selected["name"],
                "esphome_entities": {k: v for k, v in manual_entities.items() if v},
            }
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, **values},
            )

        current_id = self.config_entry.options.get(
            "esphome_device_id", self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"])
        )
        selected = next((node for node in nodes if node["device_id"] == current_id), nodes[0])
        schema = {
            vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": node["device_id"], "label": node["name"]}
                        for node in nodes
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
        labels = {
            "status": "Stan bramy",
            "position": "Pozycja bramy",
            "main_button": "Sterowanie bramą",
            "pedestrian_button": "Sterowanie furtką",
        }
        domains = {
            "status": ["sensor", "text_sensor"],
            "position": ["sensor"],
            "main_button": ["button"],
            "pedestrian_button": ["button"],
        }
        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        for role, label in labels.items():
            schema[vol.Optional(role)] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    device_id=selected["device_id"],
                    domain=domains[role],
                )
            )
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(schema),
            description_placeholders={"device": selected["name"]},
        )

    async def async_step_gate(self, user_input=None):
        """Configure the gate card without overwriting notification options."""
        if user_input is not None:
            # Each options step writes the entire options dictionary. Preserve
            # values saved by the other section instead of silently resetting them.
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
            self.config_entry.data.get(OPTION_OPENING_DIRECTION, "left"),
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
