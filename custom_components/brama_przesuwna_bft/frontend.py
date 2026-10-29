"""Automatic frontend registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "1.9.7"
_CARD_MODULE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it as a Lovelace resource where possible."""
    if not _CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: brakuje pliku karty: %s", _CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except Exception as err:  # noqa: BLE001
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.exception("Nie udało się udostępnić pliku karty BFT: %s", err)
            return

    # Storage-mode Lovelace exposes a supported resource collection API. Adding
    # the module there makes it available to the dashboard card picker.
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is not None and lovelace.resource_mode == MODE_STORAGE:
        try:
            resources = lovelace.resources
            await resources.async_get_info()
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
                    {"res_type": "module", "url": _CARD_MODULE_URL}
                )
                _LOGGER.info("Dodano zasób Lovelace karty BFT: %s", _CARD_MODULE_URL)
            elif existing.get("url") != _CARD_MODULE_URL:
                await resources.async_update_item(
                    existing["id"], {"res_type": "module", "url": _CARD_MODULE_URL}
                )
                _LOGGER.info("Zaktualizowano zasób Lovelace karty BFT: %s", _CARD_MODULE_URL)
            return
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Nie udało się dodać zasobu Lovelace karty BFT.")

    # YAML-managed resources cannot be modified by an integration. Use the
    # frontend extra-module mechanism in that case.
    try:
        add_extra_js_url(hass, _CARD_MODULE_URL)
        _LOGGER.info("Zarejestrowano moduł frontendowy karty BFT: %s", _CARD_MODULE_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Nie udało się zarejestrować modułu karty BFT.")
