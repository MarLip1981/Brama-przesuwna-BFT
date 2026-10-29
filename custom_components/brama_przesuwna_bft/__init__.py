"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.components.http import StaticPathConfig

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js?v=0.1.2"
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Expose the bundled Lovelace card JavaScript."""
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/brama_przesuwna_bft/brama-przesuwna-bft-card.js", str(_CARD_PATH), True)]
        )
    except (AttributeError, RuntimeError, OSError) as err:
        _LOGGER.warning("Nie udało się udostępnić pliku karty Lovelace: %s", err)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register or update the card resource in Lovelace storage mode."""
    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        _LOGGER.debug("Lovelace nie jest jeszcze dostępny; rejestracja zostanie ponowiona po uruchomieniu HA.")
        return

    resources = getattr(lovelace_data, "resources", None)
    if resources is None and isinstance(lovelace_data, dict):
        resources = lovelace_data.get("resources")
    if resources is None:
        _LOGGER.debug("Zasoby Lovelace nie są jeszcze dostępne; ponowienie rejestracji po uruchomieniu HA.")
        return

    try:
        # ResourceStorageCollection is lazy-loaded. Load it explicitly before
        # reading or writing, otherwise a create can overwrite existing resources.
        if hasattr(resources, "async_load"):
            await resources.async_load()

        items = resources.async_items()
        if hasattr(items, "__await__"):
            items = await items

        matching = [
            item for item in items
            if item.get("url", "").split("?")[0] == _CARD_URL.split("?")[0]
        ]
        if matching:
            current = matching[0]
            if current.get("url") != _CARD_URL:
                await resources.async_update_item(
                    current["id"],
                    {"res_type": "module", "url": _CARD_URL},
                )
                _LOGGER.info("Zaktualizowano zasób karty Brama przesuwna BFT.")
            return

        if not hasattr(resources, "async_create_item"):
            _LOGGER.warning("Automatyczna rejestracja karty nie jest obsługiwana przez aktywny tryb zasobów Lovelace.")
            return

        await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
        _LOGGER.info("Zarejestrowano zasób karty Brama przesuwna BFT: %s", _CARD_URL)
    except Exception as err:
        _LOGGER.warning(
            "Nie udało się zarejestrować zasobu karty Brama przesuwna BFT: %s",
            err,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured project entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "name": entry.data.get("name", entry.title or DEFAULT_NAME)
    }
    await _async_register_lovelace_resource(hass)

    # Lovelace may initialize after config entries on some startup paths.
    @callback
    def _retry_resource_registration(_event) -> None:
        hass.async_create_task(_async_register_lovelace_resource(hass))

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _retry_resource_registration)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured project entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    # Keep the frontend resource registered: other dashboards may still use it.
    return True
