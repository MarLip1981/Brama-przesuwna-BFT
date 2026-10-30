"""Discover the BFT ESPHome controller by its project identity."""
from __future__ import annotations

import re
import unicodedata

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

PROJECT_NAME = "MarLip1981.BramaPrzesuwnaBFT"
PROJECT_MANUFACTURER, PROJECT_MODEL = PROJECT_NAME.split(".", 1)
ROLE_HINTS = {
    "status": ("dokładny stan bramy",),
    "position": ("pozycja bramy",),
    "main_button": ("otwórz zamknij bramę", "otworz zamknij brame"),
    "pedestrian_button": ("otwórz jako furtkę", "otworz jako furtke"),
}


def _norm(value: str) -> str:
    """Normalize case, Polish diacritics, and separators for role matching."""
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def discover_esphome_gate_nodes(hass):
    """Find BFT ESPHome config entries and collect their registered devices/entities."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    results = []
    seen_devices = set()

    # Enumerate ESPHome config entries first. The registry's .devices mapping
    # is deprecated and iterating it does not provide DeviceEntry objects.
    for config_entry in hass.config_entries.async_entries("esphome"):
        devices = dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        for device in devices:
            if device.id in seen_devices:
                continue
            manufacturer = str(device.manufacturer or "").strip()
            model = str(device.model or "").strip()
            if (
                manufacturer.casefold() != PROJECT_MANUFACTURER.casefold()
                or model.casefold() != PROJECT_MODEL.casefold()
            ):
                continue

            mac_connections = [
                str(value)
                for connection_type, value in device.connections
                if connection_type == dr.CONNECTION_NETWORK_MAC
            ]
            if not mac_connections:
                continue

            device_entities = [
                entity for entity in entity_registry.entities.values()
                if entity.platform == "esphome"
                and (
                    entity.device_id == device.id
                    or entity.config_entry_id == config_entry.entry_id
                )
            ]

            mapped = {}
            for role, hints in ROLE_HINTS.items():
                normalized_hints = tuple(_norm(hint) for hint in hints)
                candidates = []
                for entity in device_entities:
                    searchable = _norm(" ".join(str(value or "") for value in (
                        entity.entity_id, entity.original_name, entity.name
                    )))
                    if any(hint in searchable for hint in normalized_hints):
                        candidates.append(entity)
                if candidates:
                    selected = next(
                        (item for item in candidates if item.device_id == device.id),
                        candidates[0],
                    )
                    mapped[role] = selected.entity_id

            seen_devices.add(device.id)
            results.append({
                "device_id": device.id,
                "node_id": config_entry.unique_id or mac_connections[0],
                "name": device.name_by_user or device.name or f"Brama BFT ({mac_connections[0]})",
                "entities": mapped,
                "manufacturer": manufacturer,
                "model": model,
            })

    return results
