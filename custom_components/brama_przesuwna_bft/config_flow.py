"""Config flow and options for Brama przesuwna BFT."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .discovery import discover_esphome_gate_nodes
from homeassistant.helpers import entity_registry as er

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



def _entity_options(node, domains):
    """Return only entities belonging to the selected ESPHome controller."""
    return [
        {"value": item["entity_id"], "label": item["label"]}
        for item in node.get("available_entities", [])
        if item.get("domain") in domains
    ]


def _entity_field(node, role, domains, default=None):
    """Build a dropdown for one mapped entity role."""
    options = _entity_options(node, domains)
    valid_values = {item["value"] for item in options}
    if default not in valid_values:
        default = None
    key = vol.Optional(role, default=default) if default else vol.Optional(role)
    return key, selector.SelectSelector(
        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
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
        """Discover and select the BFT ESPHome controller."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        if user_input is not None:
            selected = next(
                (node for node in nodes if node["device_id"] == user_input.get("esphome_device")),
                None,
            )
            if selected is None:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._device_schema(nodes),
                    errors={"base": "device_not_found"},
                )
            self._selected_bft_node = selected
            return await self.async_step_entities()
        return self.async_show_form(step_id="user", data_schema=self._device_schema(nodes))

    @staticmethod
    def _device_schema(nodes, selected_id=None):
        """Build the controller selector."""
        default = selected_id or nodes[0]["device_id"]
        return vol.Schema({
            vol.Required("esphome_device", default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        })

    async def async_step_entities(self, user_input=None):
        """Review detected entities and save the complete integration setup."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            return self.async_abort(reason="device_not_found")
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką (opcjonalnie)", ["button"]),
        }
        if user_input is not None:
            mapped = {role: user_input.get(role) for role in roles}
            if not mapped.get("status") or not mapped.get("position") or not mapped.get("main_button"):
                return self.async_show_form(
                    step_id="entities",
                    data_schema=self._entities_schema(node, roles, user_input, self.hass),
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
        defaults = {**node["entities"], OPTION_OPENING_DIRECTION: "right"}
        return self.async_show_form(
            step_id="entities",
            data_schema=self._entities_schema(node, roles, defaults, self.hass),
            description_placeholders={"device": node["name"]},
        )

    @staticmethod
    def _entities_schema(node, roles, defaults, hass=None):
        """Build reliable dropdowns from the selected ESPHome device registry entries."""
        schema = {}
        registry = er.async_get(hass) if hass is not None else None
        entries = set(node.get("config_entry_ids", []))
        for role, (label, domains) in roles.items():
            options = []
            if registry is not None:
                for entity in registry.entities.values():
                    if entity.platform != "esphome":
                        continue
                    if entity.device_id != node["device_id"] and entity.config_entry_id not in entries:
                        continue
                    if entity.entity_id.split(".", 1)[0] not in domains:
                        continue
                    options.append({
                        "value": entity.entity_id,
                        "label": entity.name or entity.original_name or entity.entity_id,
                    })
            options.sort(key=lambda item: (item["label"].casefold(), item["value"]))
            default = defaults.get(role) or node["entities"].get(role)
            key = vol.Optional(role, default=default) if default else vol.Optional(role)
            schema[key] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        schema[vol.Required(OPTION_OPENING_DIRECTION, default=defaults.get(OPTION_OPENING_DIRECTION, "right"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[{"value": "left", "label": "W lewo"}, {"value": "right", "label": "W prawo"}],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        return vol.Schema(schema)

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
        """Select the physical BFT controller before configuring its entities."""
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        current_id = self.config_entry.options.get(
            "esphome_device_id", self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"])
        )
        if user_input is not None:
            current_id = user_input.get("esphome_device", current_id)
        selected = next((node for node in nodes if node["device_id"] == current_id), None)
        if selected is None:
            return self.async_abort(reason="device_not_found")
        self._selected_bft_node = selected
        if user_input is not None:
            return await self.async_step_entities()

        schema = {
            vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_entities(self, user_input=None):
        """Automatically suggest and allow manual correction of each BFT entity."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            nodes = discover_esphome_gate_nodes(self.hass)
            current_id = self.config_entry.options.get(
                "esphome_device_id", self.config_entry.data.get("esphome_device_id")
            )
            node = next((item for item in nodes if item["device_id"] == current_id), None)
        if node is None:
            return self.async_abort(reason="device_not_found")

        if user_input is not None:
            mapped = {
                role: user_input.get(role) or node["entities"].get(role, "")
                for role in ("status", "position", "main_button", "pedestrian_button")
            }
            values = {
                "esphome_device_id": node["device_id"],
                "esphome_node_id": node["node_id"],
                "esphome_device_name": node["name"],
                "esphome_entities": {key: value for key, value in mapped.items() if value},
            }
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **values}
            )

        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką", ["button"]),
        }
        defaults = {**node["entities"], **saved}
        return self.async_show_form(
            step_id="entities",
            data_schema=BramaPrzesuwnaBFTConfigFlow._entities_schema(
                node, roles, defaults, self.hass
            ),
            description_placeholders={"device": node["name"]},
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
        )    @staticmethod
    def _entities_schema(node, roles, defaults):
        """Build dropdowns from entities discovered for this ESPHome node."""
        domains_by_role = {
            "status": ["sensor"],
            "position": ["sensor"],
            "main_button": ["button"],
            "pedestrian_button": ["button"],
        }
        schema = {}
        for role in roles:
            key, field = _entity_field(
                node, role, domains_by_role[role],
                defaults.get(role) or node["entities"].get(role),
            )
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
        """Select the physical BFT controller before configuring its entities."""
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        current_id = self.config_entry.options.get(
            "esphome_device_id", self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"])
        )
        if user_input is not None:
            current_id = user_input.get("esphome_device", current_id)
        selected = next((node for node in nodes if node["device_id"] == current_id), None)
        if selected is None:
            return self.async_abort(reason="device_not_found")
        self._selected_bft_node = selected
        if user_input is not None:
            return await self.async_step_entities()

        schema = {
            vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_entities(self, user_input=None):
        """Automatically suggest and allow manual correction of each BFT entity."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            nodes = discover_esphome_gate_nodes(self.hass)
            current_id = self.config_entry.options.get(
                "esphome_device_id", self.config_entry.data.get("esphome_device_id")
            )
            node = next((item for item in nodes if item["device_id"] == current_id), None)
        if node is None:
            return self.async_abort(reason="device_not_found")

        if user_input is not None:
            mapped = {
                role: user_input.get(role) or node["entities"].get(role, "")
                for role in ("status", "position", "main_button", "pedestrian_button")
            }
            values = {
                "esphome_device_id": node["device_id"],
                "esphome_node_id": node["node_id"],
                "esphome_device_name": node["name"],
                "esphome_entities": {key: value for key, value in mapped.items() if value},
            }
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **values}
            )

        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką", ["button"]),
        }
        defaults = {**node["entities"], **saved}
        return self.async_show_form(
            step_id="entities",
            data_schema=BramaPrzesuwnaBFTConfigFlow._entities_schema(
                node, roles, defaults, self.hass
            ),
            description_placeholders={"device": node["name"]},
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
        )        schema = {}
        for role in labels:
            key, field = _entity_field(
                node, role, domains[role],
                saved.get(role) or node["entities"].get(role),
            )
            schema[key] = field
        return self.async_show_form(step_id="user", data_schema=self._device_schema(nodes))

    @staticmethod
    def _device_schema(nodes, selected_id=None):
        """Build the controller selector."""
        default = selected_id or nodes[0]["device_id"]
        return vol.Schema({
            vol.Required("esphome_device", default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        })

    async def async_step_entities(self, user_input=None):
        """Review detected entities and save the complete integration setup."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            return self.async_abort(reason="device_not_found")
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką (opcjonalnie)", ["button"]),
        }
        if user_input is not None:
            mapped = {role: user_input.get(role) for role in roles}
            if not mapped.get("status") or not mapped.get("position") or not mapped.get("main_button"):
                return self.async_show_form(
                    step_id="entities",
                    data_schema=self._entities_schema(node, roles, user_input, self.hass),
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
        defaults = {**node["entities"], OPTION_OPENING_DIRECTION: "right"}
        return self.async_show_form(
            step_id="entities",
            data_schema=self._entities_schema(node, roles, defaults, self.hass),
            description_placeholders={"device": node["name"]},
        )

    @staticmethod
    def _entities_schema(node, roles, defaults, hass=None):
        """Build reliable dropdowns from the selected ESPHome device registry entries."""
        schema = {}
        registry = er.async_get(hass) if hass is not None else None
        entries = set(node.get("config_entry_ids", []))
        for role, (label, domains) in roles.items():
            options = []
            if registry is not None:
                for entity in registry.entities.values():
                    if entity.platform != "esphome":
                        continue
                    if entity.device_id != node["device_id"] and entity.config_entry_id not in entries:
                        continue
                    if entity.entity_id.split(".", 1)[0] not in domains:
                        continue
                    options.append({
                        "value": entity.entity_id,
                        "label": entity.name or entity.original_name or entity.entity_id,
                    })
            options.sort(key=lambda item: (item["label"].casefold(), item["value"]))
            default = defaults.get(role) or node["entities"].get(role)
            key = vol.Optional(role, default=default) if default else vol.Optional(role)
            schema[key] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        schema[vol.Required(OPTION_OPENING_DIRECTION, default=defaults.get(OPTION_OPENING_DIRECTION, "right"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[{"value": "left", "label": "W lewo"}, {"value": "right", "label": "W prawo"}],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        return vol.Schema(schema)

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
        """Select the physical BFT controller before configuring its entities."""
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        current_id = self.config_entry.options.get(
            "esphome_device_id", self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"])
        )
        if user_input is not None:
            current_id = user_input.get("esphome_device", current_id)
        selected = next((node for node in nodes if node["device_id"] == current_id), None)
        if selected is None:
            return self.async_abort(reason="device_not_found")
        self._selected_bft_node = selected
        if user_input is not None:
            return await self.async_step_entities()

        schema = {
            vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_entities(self, user_input=None):
        """Automatically suggest and allow manual correction of each BFT entity."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            nodes = discover_esphome_gate_nodes(self.hass)
            current_id = self.config_entry.options.get(
                "esphome_device_id", self.config_entry.data.get("esphome_device_id")
            )
            node = next((item for item in nodes if item["device_id"] == current_id), None)
        if node is None:
            return self.async_abort(reason="device_not_found")

        if user_input is not None:
            mapped = {
                role: user_input.get(role) or node["entities"].get(role, "")
                for role in ("status", "position", "main_button", "pedestrian_button")
            }
            values = {
                "esphome_device_id": node["device_id"],
                "esphome_node_id": node["node_id"],
                "esphome_device_name": node["name"],
                "esphome_entities": {key: value for key, value in mapped.items() if value},
            }
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **values}
            )

        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką", ["button"]),
        }
        defaults = {**node["entities"], **saved}
        return self.async_show_form(
            step_id="entities",
            data_schema=BramaPrzesuwnaBFTConfigFlow._entities_schema(
                node, roles, defaults, self.hass
            ),
            description_placeholders={"device": node["name"]},
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
        )    @staticmethod
    def _entities_schema(node, roles, defaults):
        """Build dropdowns from entities discovered for this ESPHome node."""
        domains_by_role = {
            "status": ["sensor"],
            "position": ["sensor"],
            "main_button": ["button"],
            "pedestrian_button": ["button"],
        }
        schema = {}
        for role in roles:
            key, field = _entity_field(
                node, role, domains_by_role[role],
                defaults.get(role) or node["entities"].get(role),
            )
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
        """Select the physical BFT controller before configuring its entities."""
        nodes = discover_esphome_gate_nodes(self.hass)
        if not nodes:
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors={"base": "no_matching_esphome_device"},
            )
        current_id = self.config_entry.options.get(
            "esphome_device_id", self.config_entry.data.get("esphome_device_id", nodes[0]["device_id"])
        )
        if user_input is not None:
            current_id = user_input.get("esphome_device", current_id)
        selected = next((node for node in nodes if node["device_id"] == current_id), None)
        if selected is None:
            return self.async_abort(reason="device_not_found")
        self._selected_bft_node = selected
        if user_input is not None:
            return await self.async_step_entities()

        schema = {
            vol.Required("esphome_device", default=selected["device_id"]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": node["device_id"], "label": node["name"]} for node in nodes],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
        return self.async_show_form(step_id="device", data_schema=vol.Schema(schema))

    async def async_step_entities(self, user_input=None):
        """Automatically suggest and allow manual correction of each BFT entity."""
        node = getattr(self, "_selected_bft_node", None)
        if node is None:
            nodes = discover_esphome_gate_nodes(self.hass)
            current_id = self.config_entry.options.get(
                "esphome_device_id", self.config_entry.data.get("esphome_device_id")
            )
            node = next((item for item in nodes if item["device_id"] == current_id), None)
        if node is None:
            return self.async_abort(reason="device_not_found")

        if user_input is not None:
            mapped = {
                role: user_input.get(role) or node["entities"].get(role, "")
                for role in ("status", "position", "main_button", "pedestrian_button")
            }
            values = {
                "esphome_device_id": node["device_id"],
                "esphome_node_id": node["node_id"],
                "esphome_device_name": node["name"],
                "esphome_entities": {key: value for key, value in mapped.items() if value},
            }
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **values}
            )

        saved = self.config_entry.options.get(
            "esphome_entities", self.config_entry.data.get("esphome_entities", {})
        )
        roles = {
            "status": ("Stan bramy", ["sensor"]),
            "position": ("Pozycja bramy", ["sensor"]),
            "main_button": ("Sterowanie bramą", ["button"]),
            "pedestrian_button": ("Sterowanie furtką", ["button"]),
        }
        defaults = {**node["entities"], **saved}
        return self.async_show_form(
            step_id="entities",
            data_schema=BramaPrzesuwnaBFTConfigFlow._entities_schema(
                node, roles, defaults, self.hass
            ),
            description_placeholders={"device": node["name"]},
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
