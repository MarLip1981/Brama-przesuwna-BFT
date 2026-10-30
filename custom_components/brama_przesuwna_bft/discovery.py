"""Discover BFT ESPHome controllers and their registered entities."""
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
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def discover_esphome_gate_nodes(hass):
    """Find BFT nodes through ESPHome config entries, not deprecated registry maps."""
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    results = []

    for config_entry in hass.config_entries.async_entries("esphome"):
        for device in dr.async_entries_for_config_entry(devices, config_entry.entry_id):
            manufacturer = str(device.manufacturer or "").strip()
            model = str(device.model or "").strip()
            if manufacturer.casefold() != PROJECT_MANUFACTURER.casefold():
                continue
            if model.casefold() != PROJECT_MODEL.casefold():
                continue

            macs = [
                str(value) for kind, value in device.connections
                if kind == dr.CONNECTION_NETWORK_MAC
            ]
            if not macs:
                continue

            related_devices = dr.async_entries_for_config_entry(devices, config_entry.entry_id)
            related_ids = {item.id for item in related_devices}
            registered = [
                item for item in entities.entities.values()
                if item.platform == "esphome"
                and (
                    item.config_entry_id == config_entry.entry_id
                    or item.device_id in related_ids
                )
            ]

            available = []
            mapped = {}
            for entity in registered:
                domain = entity.domain
                label = entity.name or entity.original_name or entity.entity_id
                available.append({
                    "entity_id": entity.entity_id,
                    "domain": domain,
                    "label": f"{label} ({entity.entity_id})",
                })
            for role, hints in ROLE_HINTS.items():
                normalized_hints = tuple(_norm(hint) for hint in hints)
                candidates = [
                    item for item in registered
                    if any(hint in _norm(" ".join(str(value or "") for value in (
                        item.entity_id, item.original_name, item.name
                    ))) for hint in normalized_hints)
                ]
                if candidates:
                    mapped[role] = candidates[0].entity_id

            results.append({
                "device_id": device.id,
                "node_id": config_entry.unique_id or macs[0],
                "name": device.name_by_user or device.name or f"Brama BFT ({macs[0]})",
                "entities": mapped,
                "available_entities": available,
                "manufacturer": manufacturer,
                "model": model,
            })
    return results
