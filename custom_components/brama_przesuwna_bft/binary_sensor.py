"""Binary sensor exposing configured card options and live gate data."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    OPTION_ENTRANCE_LIGHTING,
    OPTION_LAMP_MODE,
    OPTION_OPENING_DIRECTION,
    OPTION_PEDESTRIAN_MODE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the option sensor consumed by the Lovelace card and Jarvis."""
    entity = PedestrianModeSensor(entry)
    async_add_entities([entity])

    entities = entry.options.get(
        "esphome_entities", entry.data.get("esphome_entities", {})
    )
    watched = [
        entity_id
        for entity_id in (entities.get("status"), entities.get("position"))
        if entity_id
    ]

    async def _refresh_gate_data(event: Event) -> None:
        """Refresh exposed attributes when the configured gate data changes."""
        entity.async_write_ha_state()

    if watched:
        entry.async_on_unload(
            async_track_state_change_event(hass, watched, _refresh_gate_data)
        )


class PedestrianModeSensor(BinarySensorEntity):
    """Expose integration settings and live gate values for external displays."""

    _attr_has_entity_name = False
    _attr_name = "Brama przesuwna BFT tryb furtki"
    _attr_icon = "mdi:walk"
    _attr_entity_registry_enabled_default = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_pedestrian_mode_enabled"

    def _option(self, key: str, default):
        """Read current option, falling back to initial setup data."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    def _entities(self) -> dict:
        """Return the currently configured ESPHome entity mapping."""
        return self._entry.options.get(
            "esphome_entities", self._entry.data.get("esphome_entities", {})
        )

    @property
    def is_on(self) -> bool:
        """Return whether pedestrian-gate mode is enabled."""
        return bool(self._option(OPTION_PEDESTRIAN_MODE, False))

    @property
    def extra_state_attributes(self) -> dict:
        """Expose settings, entity IDs and live values to Jarvis."""
        entities = self._entities()
        status_entity = entities.get("status")
        position_entity = entities.get("position")
        status = (
            self.hass.states.get(status_entity)
            if self.hass and status_entity
            else None
        )
        position = (
            self.hass.states.get(position_entity)
            if self.hass and position_entity
            else None
        )

        try:
            gate_position = (
                float(position.state)
                if position and position.state not in ("unknown", "unavailable")
                else None
            )
        except (TypeError, ValueError):
            gate_position = None

        return {
            "opening_direction": self._option(OPTION_OPENING_DIRECTION, "left"),
            "lamp_mode": self._option(OPTION_LAMP_MODE, "auto"),
            "entrance_lighting_enabled": bool(self._option(OPTION_ENTRANCE_LIGHTING, False)),
            "esphome_device": self._entry.options.get(
                "esphome_device_name", self._entry.data.get("esphome_device_name")
            ),
            "esphome_node_id": self._entry.options.get(
                "esphome_node_id", self._entry.data.get("esphome_node_id")
            ),
            "entities": entities,
            "status_entity": status_entity or "",
            "position_entity": position_entity or "",
            "main_button_entity": entities.get("main_button") or "",
            "pedestrian_button_entity": entities.get("pedestrian_button") or "",
            "gate_status": status.state if status else "unknown",
            "gate_position": gate_position,
        }
