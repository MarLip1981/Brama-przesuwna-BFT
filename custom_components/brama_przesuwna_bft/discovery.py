"""Discover the BFT ESPHome controller by its project identity."""
from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

PROJECT_NAME = "MarLip1981.BramaPrzesuwnaBFT"
ROLE_HINTS = {
    "status": ("dokładny stan bramy",),
    "position": ("pozycja bramy",),
    "main_button": ("otwórz / zamknij bramę", "otworz / zamknij brame", "otworz zamknij brame"),
    "pedestrian_button": ("otwórz jako furtkę", "otworz jako furtke"),
}


def _norm(value: str) -> str:
    """Normalize case and Polish diacritics for role matching."""
    import unicodedata
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def discover_esphome_gate_nodes(hass):
    """Find BFT controllers using ESPHome project metadata, not user-facing names."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    results = []

    for device in device_registry.devices.values():
        identifiers = {
            (str(pair[0]), str(pair[1]))
            for pair in device.identifiers
            if isinstance(pair, (tuple, list)) and len(pair) == 2
        }
        esphome_ids = [value for domain, value in identifiers if domain == "esphome"]
        esphome_entries = [
            entry_id for entry_id in device.config_entries
            if (entry := hass.config_entries.async_get_entry(entry_id)) is not None
            and entry.domain == "esphome"
        ]
        if not esphome_ids or not esphome_entries:
            continue

        # ESPHome project metadata is exposed in HA device manufacturer/model.
        # Manufacturer is the stable project name; never use friendly device/entity names
        # as the identity of this integration.
        manufacturer = str(device.manufacturer or "").strip()
        if manufacturer.casefold() != PROJECT_NAME.casefold():
            continue

        mapped = {}
        device_entities = [
            entity for entity in entity_registry.entities.values()
            if entity.device_id == device.id and entity.platform == "esphome"
        ]
        for role, hints in ROLE_HINTS.items():
            normalized_hints = tuple(_norm(hint) for hint in hints)
            for entity in device_entities:
                searchable = _norm(" ".join(str(value or "") for value in (
                    entity.entity_id, entity.original_name, entity.name
                )))
                if any(hint in searchable for hint in normalized_hints):
                    mapped[role] = entity.entity_id
                    break

        results.append({
            "device_id": device.id,
            "node_id": esphome_ids[0],
            "name": device.name_by_user or device.name or esphome_ids[0],
            "entities": mapped,
            "manufacturer": manufacturer,
            "model": device.model or "",
        })

    return results
