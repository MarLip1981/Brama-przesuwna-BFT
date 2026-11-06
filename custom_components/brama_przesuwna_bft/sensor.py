"""Sensor interface for external displays such as Jarvis."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up the dedicated external-display data entity."""
    entity = JarvisGateSensor(entry)
    async_add_entities([entity])

    entities = entry.options.get(
        "esphome_entities", entry.data.get("esphome_entities", {})
    )
    watched = [
        entity_id
        for entity_id in (entities.get("status"), entities.get("position"))
        if entity_id
    ]

    if watched:
        async def _refresh_gate_data(event: Event) -> None:
            """Refresh attributes when the configured gate data changes."""
            entity.async_write_ha_state()

        entry.async_on_unload(
            async_track_state_change_event(hass, watched, _refresh_gate_data)
        )


class JarvisGateSensor(SensorEntity):
    """Publish configured gate data for external displays, separately from the wicket switch."""

    _attr_has_entity_name = False
    _attr_name = "Brama przesuwna BFT Jarvis"
    _attr_icon = "mdi:gate"
    _attr_entity_registry_enabled_default = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_jarvis"

    @property
    def native_value(self) -> str:
        """Return a stable state; live gate data is exposed in attributes."""
        return "ready"

    def _option(self, key: str, default):
        """Read current option, falling back to initial setup data."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    def _entities(self) -> dict:
        """Return the currently configured ESPHome entity mapping."""
        return self._entry.options.get(
            "esphome_entities", self._entry.data.get("esphome_entities", {})
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Expose gate state, position, settings and configured control entity IDs."""
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
            "entrance_lighting_enabled": bool(
                self._option(OPTION_ENTRANCE_LIGHTING, False)
            ),
            "pedestrian_mode_enabled": bool(
                self._option(OPTION_PEDESTRIAN_MODE, False)
            ),
            "esphome_device": self._entry.options.get(
                "esphome_device_name", self._entry.data.get("esphome_device_name")
            ),
            "esphome_node_id": self._entry.options.get(
                "esphome_node_id", self._entry.data.get("esphome_node_id")
            ),
            "status_entity": status_entity or "",
            "position_entity": position_entity or "",
            "main_button_entity": entities.get("main_button") or "",
            "pedestrian_button_entity": entities.get("pedestrian_button") or "",
            "gate_status": status.state if status else "unknown",
            "gate_position": gate_position,
        }
