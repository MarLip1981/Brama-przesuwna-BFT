"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "1.9.4"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it using the active Lovelace resource mode."""
    if not _CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: brakuje pliku karty: %s", _CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except Exception as err:  # noqa: BLE001
        # A repeated setup can encounter a path that was already registered.
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.exception("Nie udało się udostępnić pliku karty BFT: %s", err)
            return

    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None) if lovelace else None
    resource_mode = getattr(lovelace, "resource_mode", None) if lovelace else None

    if resource_mode == "storage" and resources is not None:
        try:
            # ResourceStorageCollection loads lazily. Explicitly load it before
            # inspecting or creating items; otherwise async_items() may be empty
            # and creating an item can overwrite the user's existing resources.
            await resources.async_load()
            existing = next(
                (
                    item
                    for item in resources.async_items()
                    if item.get("url", "").split("?", 1)[0] == _CARD_URL
                ),
                None,
            )
            if existing is None:
                await resources.async_create_item(
                    {"res_type": "module", "url": _RESOURCE_URL}
                )
                _LOGGER.info("Dodano kartę BFT do zasobów Lovelace: %s", _RESOURCE_URL)
            elif existing.get("url") != _RESOURCE_URL:
                await resources.async_update_item(
                    existing["id"],
                    {"res_type": "module", "url": _RESOURCE_URL},
                )
                _LOGGER.info("Zaktualizowano zasób karty BFT: %s", _RESOURCE_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Nie udało się dodać karty BFT do zasobów Lovelace.")
        return

    # YAML resource mode is read-only, so use Home Assistant's extra-module
    # mechanism there as the supported fallback.
    try:
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.info("Zarejestrowano moduł karty BFT przez extra_module_url: %s", _RESOURCE_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Nie udało się zarejestrować modułu karty BFT.")
