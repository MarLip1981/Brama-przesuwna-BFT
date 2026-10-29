"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.http import StaticPathConfig

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js?v=0.1.0"
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
    """Register the card resource when Lovelace uses storage mode."""
    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        _LOGGER.warning(
            "Karta Brama przesuwna BFT: Lovelace nie jest dostępny; "
            "zasób może wymagać ręcznego dodania w Ustawienia → Pulpity."
        )
        return

    resources = getattr(lovelace_data, "resources", None)
    if resources is None and isinstance(lovelace_data, dict):
        resources = lovelace_data.get("resources")
    if resources is None:
        _LOGGER.warning(
            "Karta Brama przesuwna BFT: nie znaleziono kolekcji zasobów Lovelace."
        )
        return

    try:
        # ResourceStorageCollection is lazy-loaded on current Home Assistant.
        if hasattr(resources, "async_load") and not getattr(resources, "loaded", True):
            await resources.async_load()
        items = resources.async_items()
        if hasattr(items, "__await__"):
            items = await items
        if any(item.get("url", "").split("?")[0] == _CARD_URL.split("?")[0] for item in items):
            return
        await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
        _LOGGER.info("Automatycznie dodano kartę Brama przesuwna BFT do zasobów Lovelace.")
    except (AttributeError, RuntimeError, TypeError, ValueError) as err:
        _LOGGER.warning(
            "Nie udało się automatycznie zarejestrować karty Lovelace: %s. "
            "Możesz dodać zasób %s ręcznie w Ustawienia → Pulpity → Zasoby.",
            err,
            _CARD_URL,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured project entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "name": entry.data.get("name", entry.title or DEFAULT_NAME)
    }
    await _async_register_lovelace_resource(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured project entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    # Keep the frontend resource registered: other dashboards may still use it.
    return True
