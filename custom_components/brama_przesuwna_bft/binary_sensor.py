"""Binary sensor exposing the configured pedestrian-mode option."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OPTION_PEDESTRIAN_MODE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the mode sensor consumed by the Lovelace card."""
    async_add_entities([PedestrianModeSensor(entry)])


class PedestrianModeSensor(BinarySensorEntity):
    """Reflect whether pedestrian-gate mode is enabled in integration options."""

    _attr_has_entity_name = False
    _attr_name = "Brama przesuwna BFT tryb furtki"
    _attr_icon = "mdi:walk"
    _attr_entity_registry_enabled_default = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_pedestrian_mode_enabled"

    @property
    def is_on(self) -> bool:
        """Return the configured option value."""
        return bool(self._entry.options.get(OPTION_PEDESTRIAN_MODE, False))
