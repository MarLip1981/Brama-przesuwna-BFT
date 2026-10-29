"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "0.1.6"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it using Home Assistant's Lovelace APIs."""
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except Exception as err:  # noqa: BLE001
        # Re-adding an integration entry can encounter the existing route.
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.warning("Nie udało się udostępnić pliku karty Brama przesuwna BFT: %s", err)
            return

    # Use HA's official typed key. A literal "lovelace" key does not reliably
    # point to the Lovelace data object and was the reason registration failed.
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.warning(
            "Plik karty jest dostępny pod %s, ale dane Lovelace nie są jeszcze dostępne.",
            _CARD_URL,
        )
        return

    # YAML resource mode is read-only; use HA's frontend helper to inject the JS.
    if getattr(lovelace, "resource_mode", "storage") == "yaml":
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.info("Zarejestrowano kartę Brama przesuwna BFT jako dodatkowy moduł JS.")
        return

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.warning("Nie znaleziono rejestru zasobów Lovelace dla karty BFT.")
        return

    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()

        items = list(resources.async_items())
        matching = [
            item for item in items
            if str(item.get("url", "")).split("?", 1)[0] == _CARD_URL
        ]
        if matching:
            primary = matching[0]
            if primary.get("url") != _RESOURCE_URL or primary.get("res_type") != "module":
                await resources.async_update_item(
                    primary["id"], {"res_type": "module", "url": _RESOURCE_URL}
                )
            for duplicate in matching[1:]:
                await resources.async_delete_item(duplicate["id"])
            _LOGGER.info("Zasób karty Brama przesuwna BFT jest zarejestrowany: %s", _RESOURCE_URL)
            return

        await resources.async_create_item({"res_type": "module", "url": _RESOURCE_URL})
        _LOGGER.info("Automatycznie dodano zasób karty Brama przesuwna BFT: %s", _RESOURCE_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Nie udało się automatycznie zarejestrować zasobu karty BFT.")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Allow Home Assistant to load the integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register the frontend card when the user adds the integration."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "name": entry.data.get("name", entry.title or DEFAULT_NAME)
    }
    await _async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry without removing the shared dashboard resource."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
