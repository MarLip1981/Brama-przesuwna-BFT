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
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js?v=0.1.3"
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Expose the bundled Lovelace card JavaScript."""
    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/brama_przesuwna_bft/brama-przesuwna-bft-card.js",
                    str(_CARD_PATH),
                    True,
                )
            ]
        )
    except (AttributeError, RuntimeError, OSError) as err:
        _LOGGER.warning("Nie udało się udostępnić pliku karty Lovelace: %s", err)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Register or update the card resource in Lovelace storage mode."""
    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        _LOGGER.debug("Lovelace nie jest jeszcze dostępny.")
        return False

    resources = getattr(lovelace_data, "resources", None)
    if resources is None and isinstance(lovelace_data, dict):
        resources = lovelace_data.get("resources")
    if resources is None:
        _LOGGER.debug("Zasoby Lovelace nie są jeszcze dostępne.")
        return False

    try:
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
            return True

        if not hasattr(resources, "async_create_item"):
            _LOGGER.error(
                "Automatyczna rejestracja karty nie jest obsługiwana przez aktywny tryb zasobów Lovelace."
            )
            return False

        await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
        _LOGGER.info("Zarejestrowano zasób karty Brama przesuwna BFT: %s", _CARD_URL)
        return True
    except Exception as err:
        _LOGGER.warning("Nie udało się zarejestrować zasobu karty Brama przesuwna BFT: %s", err)
        return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured project entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "name": entry.data.get("name", entry.title or DEFAULT_NAME)
    }

    async def _register_with_retries() -> None:
        # The entry may be configured after HA has already started.
        for delay in (0, 5, 15, 30):
            if delay:
                await asyncio.sleep(delay)
            if await _async_register_lovelace_resource(hass):
                return
        _LOGGER.error(
            "Karta Brama przesuwna BFT nie została automatycznie zarejestrowana po kilku próbach."
        )

    hass.async_create_task(_register_with_retries())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured project entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    # Keep the frontend resource registered: other dashboards may still use it.
    return True
