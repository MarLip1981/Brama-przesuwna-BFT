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
_CARD_VERSION = "1.9.2"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def async_setup_frontend(hass: HomeAssistant, attempt: int = 0) -> None:
    """Serve and register the card module globally in Home Assistant's frontend."""
    if not _CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: brakuje pliku karty: %s", _CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except Exception as err:  # noqa: BLE001
        # The path may already have been registered by an earlier setup call.
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.exception("Nie udało się udostępnić pliku karty BFT: %s", err)
            return

    try:
        # Register the module through Home Assistant's supported frontend API.
        # This works independently of Lovelace storage/YAML resource management.
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.info("Zarejestrowano moduł karty BFT: %s", _RESOURCE_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Nie udało się zarejestrować modułu karty BFT.")
