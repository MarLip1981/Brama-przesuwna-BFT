"""Config flow and options for Brama przesuwna BFT."""
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
from .discovery import discover_esphome_gate_nodes


ROLE_DOMAINS = {
    "status": ["sensor"],
    "position": ["sensor"],
    "main_button": ["button"],
    "pedestrian_button": ["button"],
}
ROLE_LABELS = {
    "status": "Stan bramy",
    "position": "Pozycja bramy",
    "main_button": "Sterowanie bramą",
    "pedestrian_button": "Sterowanie furtką",
}


def _entity_field(node, role, default=None):
    """Create a dropdown containing only entities found for this ESPHome node."""
    options = [
        {"value": item["entity_id"], "label": item["label"]}
        for item in node.get("available_entities", [])
        if item.get("domain") in ROLE_DOMAINS[role]
    ]
    allowed = {item["value"] for item in options}
    if default not in allowed:
        default = node.get("entities", {}).get(role)
    if default not in allowed:
        default = None
    key = vol.Optional(role, default=default) if default else vol.Optional(role)
    return key, selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _entities_schema(node, defaults):
    """Build entity selectors and the opening-direction selector."""
    schema = {}
    for role in ROLE_DOMAINS:
        key, field = _entity_field(node, role, defaults.get(role))
        schema[key] = field
    schema[vol.Required(
        OPTION_OPENING_DIRECTION,
        default=defaults.get(OPTION_OPENING_DIRECTION, "right"),
    )] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": "left", "label": "W lewo"},
                {"value": "right", "label": "W prawo"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
    return vol.Schema(schema)


def _gate_schema(pedestrian_default, direction_default):
    return vol.Schema({
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
    })


def _notification_schema(hass, entry):
    services = hass.services.async_services().get("notify", {})
    targets = sorted({DEFAULT_NOTIFY_TARGET, *services})
    selected = entry.options.get(
        OPTION_NOTIFY_TARGETS,
        entry.data.get(OPTION_NOTIFY_TARGETS, [DEFAULT_NOTIFY_TARGET]),
    )
    return vol.Schema({
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
                options=[{"value": name, "label": f"notify.{name}"} for name in targets],
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    })


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one BFT sliding gate."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=self._device_schema(nodes)
            )
        selected = next(
            (node for node in nodes if node["device_id"] == user_input.get("esphome_device")),
            None,
        )
        if selected is None:
            return self.async_show_form(
                step_id="user", data_schema=self._device_schema(nodes),
                errors={"base": "device_not_found"},
            )
        self._selected_bft_node = selected
        return await self.async_step_entities()

    @staticmethod
    def _device_schema(nodes):
        return vol.Schema({
            vol.Required("esphome_device", default=nodes[0]["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": node["device_id"], "label": node["name"]}
                        for node in nodes
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        })

    async def async_step_entities(self, user_input=None):
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            return self.async_abort(reason="device_not_found")
        if user_input is None:
            return self.async_show_form(
                step_id="entities",
                data_schema=_entities_schema(
                    node, {**node.get("entities", {}), OPTION_OPENING_DIRECTION: "right"}
                ),
                description_placeholders={"device": node["name"]},
            )

        mapped = {role: user_input.get(role) for role in ROLE_DOMAINS}
        if not all(mapped.get(role) for role in ("status", "position", "main_button")):
            return self.async_show_form(
                step_id="entities",
                data_schema=_entities_schema(node, {**user_input, **node.get("entities", {})}),
                errors={"base": "required_entities"},
                description_placeholders={"device": node["name"]},
            )
        return self.async_create_entry(
            title=DEFAULT_NAME,
            data={
                "esphome_device_id": node["device_id"],
                "esphome_node_id": node["node_id"],
                "esphome_device_name": node["name"],
                "esphome_entities": {key: value for key, value in mapped.items() if value},
                OPTION_PEDESTRIAN_MODE: bool(mapped.get("pedestrian_button")),
                OPTION_OPENING_DIRECTION: user_input.get(OPTION_OPENING_DIRECTION, "right"),
                OPTION_NOTIFY_OPEN: False,
                OPTION_NOTIFY_CLOSED: False,
                OPTION_NOTIFY_TARGETS: [DEFAULT_NOTIFY_TARGET],
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return BramaPrzesuwnaBFTOptionsFlow(config_entry)


class BramaPrzesuwnaBFTOptionsFlow(config_entries.OptionsFlowWithReload):
    """Configure mapped entities, card behavior and notifications."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init", menu_options=["device", "gate", "notifications"]
        )

    async def async_step_device(self, user_input=None):
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device", data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        current_id = self.config_entry.options.get(
            "esphome_device_id",
            self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"]),
        )
        if user_input is None:
            selected = next((n for n in nodes if n["device_id"] == current_id), nodes[0])
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({
                    vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": n["device_id"], "label": n["name"]} for n in nodes],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }),
            )
        node = next((n for n in nodes if n["device_id"] == user_input.get("esphome_device")), None)
        if node is None:
            return self.async_abort(reason="device_not_found")
        self._selected_bft_node = node
        return await self.async_step_entities()

    async def async_step_entities(self, user_input=None):
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            nodes = discover_esphome_gate_nodes(self.hass)
            saved_id = self.config_entry.options.get(
                "esphome_device_id", self.config_entry.data.get("esphome_device_id")
            )
            node = next((n for n in nodes if n["device_id"] == saved_id), None)
        if node is None:
            return self.async_abort(reason="device_not_found")
        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        if user_input is None:
            return self.async_show_form(
                step_id="entities",
                data_schema=_entities_schema(node, {**node.get("entities", {}), **saved}),
                description_placeholders={"device": node["name"]},
            )
        mapped = {
            role: user_input.get(role) or node.get("entities", {}).get(role)
            for role in ROLE_DOMAINS
        }
        if not all(mapped.get(role) for role in ("status", "position", "main_button")):
            return self.async_show_form(
                step_id="entities",
                data_schema=_entities_schema(node, {**mapped, **user_input}),
                errors={"base": "required_entities"},
                description_placeholders={"device": node["name"]},
            )
        values = {
            "esphome_device_id": node["device_id"],
            "esphome_node_id": node["node_id"],
            "esphome_device_name": node["name"],
            "esphome_entities": {key: value for key, value in mapped.items() if value},
        }
        return self.async_create_entry(title="", data={**self.config_entry.options, **values})

    async def async_step_gate(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input}
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
            step_id="gate", data_schema=_gate_schema(pedestrian, direction)
        )

    async def async_step_notifications(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input}
            )
        return self.async_show_form(
            step_id="notifications",
            data_schema=_notification_schema(self.hass, self.config_entry),
        )
