"""Discover the BFT ESPHome controller by its project identity."""
from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

PROJECT_NAME = "MarLip1981.BramaPrzesuwnaBFT"
PROJECT_MANUFACTURER, PROJECT_MODEL = PROJECT_NAME.split(".", 1)
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
        # The main ESPHome device is registered by its network-MAC connection,
        # not by an ("esphome", ...) identifier. That identifier is used for
        # ESPHome sub-devices. Identify the main physical node through the
        # ESPHome config entry attached to the device registry record.
        esphome_entries = [
            entry for entry_id in device.config_entries
            if (entry := hass.config_entries.async_get_entry(entry_id)) is not None
            and entry.domain == "esphome"
        ]
        if not esphome_entries:
            continue

        # Only accept the main ESPHome device, which has a network-MAC
        # connection. Sub-devices may inherit project manufacturer/model.
        mac_connections = [
            str(value) for connection_type, value in device.connections
            if connection_type == dr.CONNECTION_NETWORK_MAC
        ]
        if not mac_connections:
            continue

        # Home Assistant splits ESPHome project_name at the first dot:
        # "MarLip1981.BramaPrzesuwnaBFT" becomes manufacturer="MarLip1981"
        # and model="BramaPrzesuwnaBFT". Match both stable fields, never the
        # friendly device/entity names.
        manufacturer = str(device.manufacturer or "").strip()
        model = str(device.model or "").strip()
        if (
            manufacturer.casefold() != PROJECT_MANUFACTURER.casefold()
            or model.casefold() != PROJECT_MODEL.casefold()
        ):
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
            "node_id": esphome_entries[0].unique_id or mac_connections[0],
            "name": device.name_by_user or device.name or esphome_ids[0],
            "entities": mapped,
            "manufacturer": manufacturer,
            "model": model,
        })

    return results
