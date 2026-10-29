"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "1.9.1"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"
_RETRY_DELAY = 5
_MAX_RETRIES = 12


def _schedule_retry(hass: HomeAssistant, attempt: int) -> None:
    """Retry registration while Home Assistant is still initializing Lovelace."""
    if attempt >= _MAX_RETRIES:
        _LOGGER.error(
            "Nie udało się zarejestrować karty BFT po %s próbach. "
            "Sprawdź wcześniejsze błędy rejestracji w logu.",
            attempt,
        )
        return

    async_call_later(
        hass,
        _RETRY_DELAY,
        lambda _now: hass.async_create_task(async_setup_frontend(hass, attempt + 1)),
    )


async def async_setup_frontend(hass: HomeAssistant, attempt: int = 0) -> None:
    """Serve the card and register it in Lovelace, including YAML mode."""
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
            _LOGGER.warning("Nie udało się udostępnić pliku karty BFT: %s", err)
            _schedule_retry(hass, attempt)
            return

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.debug("Lovelace nie jest jeszcze dostępny; ponawiam rejestrację karty BFT.")
        _schedule_retry(hass, attempt)
        return

    if getattr(lovelace, "resource_mode", "storage") == "yaml":
        try:
            add_extra_js_url(hass, _RESOURCE_URL)
            _LOGGER.info("Zarejestrowano kartę BFT jako dodatkowy moduł JS: %s", _RESOURCE_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Nie udało się zarejestrować modułu JS karty BFT w trybie YAML.")
            _schedule_retry(hass, attempt)
        return

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.debug("Rejestr zasobów Lovelace nie jest jeszcze dostępny; ponawiam rejestrację.")
        _schedule_retry(hass, attempt)
        return

    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()

        existing = list(resources.async_items())
        matching = [
            item for item in existing
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
            _LOGGER.info("Zasób karty BFT jest zarejestrowany: %s", _RESOURCE_URL)
            return

        await resources.async_create_item({"res_type": "module", "url": _RESOURCE_URL})
        _LOGGER.info("Automatycznie dodano zasób karty BFT do Lovelace: %s", _RESOURCE_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Nie udało się automatycznie dodać zasobu karty BFT.")
        _schedule_retry(hass, attempt)
