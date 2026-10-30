"""Discover ESPHome devices that may control the BFT gate."""
from __future__ import annotations

import unicodedata

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

ROLE_HINTS = {
    "status": ("dokładny stan bramy", "dokladny stan bramy"),
    "position": ("pozycja bramy",),
    "main_button": (
        "otwórz / zamknij bramę",
        "otworz / zamknij brame",
        "otworz zamknij brame",
    ),
    "pedestrian_button": ("otwórz jako furtkę", "otworz jako furtke"),
}
DEFAULT_DEVICE_NAME = "brama wjazdowa"
FALLBACK_NAME_PARTS = ("brama", "wjazd")


def _normalize(value: str) -> str:
    """Normalize case and Polish diacritics for forgiving name matching."""
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in value if not unicodedata.combining(char))


def discover_esphome_gate_nodes(hass):
    """Find likely gate ESPHome devices, even when entity names are unfamiliar."""
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    exact = []
    fallback = []

    for device in devices.devices.values():
        esphome_ids = [
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == "esphome"
        ]
        if not esphome_ids:
            continue

        node_id = esphome_ids[0]
        display_name = device.name or device.name_by_user or node_id
        names = [_normalize(value) for value in (display_name, device.name_by_user, node_id)]
        searchable_names = [name for name in names if name]

        device_entities = [
            entity for entity in entities.entities.values()
            if entity.device_id == device.id and entity.platform == "esphome"
        ]
        mapped = {}
        for role, hints in ROLE_HINTS.items():
            normalized_hints = tuple(_normalize(hint) for hint in hints)
            for entity in device_entities:
                searchable = _normalize(" ".join(
                    str(value or "")
                    for value in (entity.entity_id, entity.original_name, entity.name)
                ))
                if any(hint in searchable for hint in normalized_hints):
                    mapped[role] = entity.entity_id
                    break

        candidate = {
            "device_id": device.id,
            "node_id": node_id,
            "name": display_name,
            "entities": mapped,
        }
        if any(name == DEFAULT_DEVICE_NAME for name in searchable_names):
            exact.append(candidate)
        elif any(part in name for name in searchable_names for part in FALLBACK_NAME_PARTS):
            fallback.append(candidate)

    # Exact match wins; otherwise expose every partial name match for manual selection.
    return exact or fallback
