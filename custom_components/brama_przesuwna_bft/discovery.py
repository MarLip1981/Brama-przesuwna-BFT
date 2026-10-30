"""Discover the ESPHome node and its entities already registered in Home Assistant."""
from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

ROLE_HINTS = {
    "status": ("dokładny stan bramy", "dokladny stan bramy"),
    "position": ("pozycja bramy",),
    "main_button": ("otwórz / zamknij bramę", "otworz / zamknij brame"),
    "pedestrian_button": ("otwórz jako furtkę", "otworz jako furtke"),
}


def discover_esphome_gate_nodes(hass):
    """Return ESPHome devices that expose the expected BFT gate firmware entities."""
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    found = []

    for device in devices.devices.values():
        esphome_ids = [
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == "esphome"
        ]
        if not esphome_ids:
            continue

        device_entities = [
            entity for entity in entities.entities.values()
            if entity.device_id == device.id and entity.platform == "esphome"
        ]
        mapped = {}
        for role, hints in ROLE_HINTS.items():
            for entity in device_entities:
                searchable = " ".join(
                    str(value or "")
                    for value in (
                        entity.entity_id,
                        entity.original_name,
                        entity.name,
                    )
                ).casefold()
                if any(hint in searchable for hint in hints):
                    mapped[role] = entity.entity_id
                    break

        # A valid gate node must at least provide its state, position and
        # the main gate command. The pedestrian command is optional.
        if {"status", "position", "main_button"} <= mapped.keys():
            found.append({
                "device_id": device.id,
                "node_id": esphome_ids[0],
                "name": device.name or device.name_by_user or esphome_ids[0],
                "entities": mapped,
            })

    return found
