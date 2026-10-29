"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "0.1.6"
_VERSIONED_CARD_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def _async_register_resource(hass: HomeAssistant) -> bool:
    """Register the card as a Lovelace resource when storage mode is available."""
    lovelace: Any = hass.data.get(LOVELACE_DATA)
    resources = getattr(lovelace, "resources", None)
    if resources is None:
        return False

    try:
        if not getattr(resources, "loaded", False):
            await resources.async_load()

        for resource in resources.async_items():
            url = str(resource.get("url", ""))
            if url.split("?", 1)[0] == _CARD_URL:
                resource_id = resource.get("id")
                if url != _VERSIONED_CARD_URL and resource_id is not None:
                    await resources.async_update_item(resource_id, {"url": _VERSIONED_CARD_URL})
                return True

        await resources.async_create_item({"res_type": "module", "url": _VERSIONED_CARD_URL})
        _LOGGER.info("Brama przesuwna BFT: zarejestrowano zasób karty Lovelace.")
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Brama przesuwna BFT: nie udało się zarejestrować zasobu Lovelace.")
        return False


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it independently of the config entry."""
    if not _CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: brakuje pliku karty: %s", _CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except RuntimeError:
        # The route can remain registered after reloading the integration.
        _LOGGER.debug("Brama przesuwna BFT: ścieżka karty jest już zarejestrowana.")
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Brama przesuwna BFT: nie udało się udostępnić pliku karty.")
        return

    if await _async_register_resource(hass):
        return

    try:
        add_extra_js_url(hass, _VERSIONED_CARD_URL)
        _LOGGER.warning(
            "Brama przesuwna BFT: użyto awaryjnej rejestracji modułu JS; "
            "jeśli karta nie pojawi się na liście, ponowna próba nastąpi przy ładowaniu wpisu integracji."
        )
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Brama przesuwna BFT: awaryjna rejestracja karty nie powiodła się.")
