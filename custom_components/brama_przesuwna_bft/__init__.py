"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)
_CARD_VERSION = "0.1.5"
_CARD_URL = f"/brama_przesuwna_bft/brama-przesuwna-bft-card.js?v={_CARD_VERSION}"
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_STATIC_PATH = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Expose the bundled Lovelace card JavaScript."""
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_STATIC_PATH, str(_CARD_PATH), True)]
        )
        _LOGGER.debug("Udostępniono plik karty Brama przesuwna BFT: %s", _STATIC_PATH)
    except (AttributeError, RuntimeError, OSError) as err:
        _LOGGER.warning("Nie udało się udostępnić pliku karty Lovelace: %s", err)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Register or update the card resource when Lovelace uses storage resources."""
    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        _LOGGER.debug("Rejestracja karty: dane Lovelace nie są jeszcze dostępne.")
        return False

    resources = getattr(lovelace_data, "resources", None)
    if resources is None and isinstance(lovelace_data, dict):
        resources = lovelace_data.get("resources")
    if resources is None:
        _LOGGER.debug("Rejestracja karty: kolekcja zasobów Lovelace jest niedostępna.")
        return False

    if not hasattr(resources, "async_create_item"):
        _LOGGER.error(
            "Nie można automatycznie dodać karty Brama przesuwna BFT: "
            "zasoby Lovelace są w trybie YAML lub nie obsługują zapisu."
        )
        return False

    try:
        if hasattr(resources, "async_load"):
            await resources.async_load()

        items = resources.async_items()
        if hasattr(items, "__await__"):
            items = await items

        matching = [
            item for item in items
            if item.get("url", "").split("?")[0] == _STATIC_PATH
        ]
        if matching:
            current = matching[0]
            if current.get("url") != _CARD_URL:
                await resources.async_update_item(
                    current["id"], {"res_type": "module", "url": _CARD_URL}
                )
                _LOGGER.info("Zaktualizowano zasób karty Brama przesuwna BFT do wersji %s.", _CARD_VERSION)
            return True

        await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
        _LOGGER.info("Zarejestrowano zasób karty Brama przesuwna BFT: %s", _CARD_URL)
        return True
    except Exception:
        _LOGGER.exception("Nie udało się zarejestrować zasobu karty Brama przesuwna BFT.")
        return False


async def _async_register_with_retries(hass: HomeAssistant) -> None:
    """Retry registration while Home Assistant finishes initializing Lovelace."""
    for delay in (0, 5, 15, 30, 60):
        if delay:
            await asyncio.sleep(delay)
        if await _async_register_lovelace_resource(hass):
            return
    _LOGGER.error(
        "Karta Brama przesuwna BFT nie została zarejestrowana automatycznie. "
        "Sprawdź wcześniejsze komunikaty dotyczące zasobów Lovelace."
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured project entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "name": entry.data.get("name", entry.title or DEFAULT_NAME)
    }
    hass.async_create_task(_async_register_with_retries(hass))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured project entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    # Keep the frontend resource registered: other dashboards may still use it.
    return True
