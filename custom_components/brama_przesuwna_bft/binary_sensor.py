"""Binary sensor exposing configured card options."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OPTION_OPENING_DIRECTION, OPTION_PEDESTRIAN_MODE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the option sensor consumed by the Lovelace card."""
    async_add_entities([PedestrianModeSensor(entry)])


class PedestrianModeSensor(BinarySensorEntity):
    """Expose pedestrian mode and gate direction to the frontend."""

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

    @property
    def is_on(self) -> bool:
        """Return whether pedestrian-gate mode is enabled."""
        return bool(self._option(OPTION_PEDESTRIAN_MODE, False))

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the configured opening direction to the card."""
        return {
            "opening_direction": self._option(OPTION_OPENING_DIRECTION, "left"),
            "esphome_device": self._entry.data.get("esphome_device_name"),
            "esphome_node_id": self._entry.data.get("esphome_node_id"),
            "entities": self._entry.data.get("esphome_entities", {}),
        }
