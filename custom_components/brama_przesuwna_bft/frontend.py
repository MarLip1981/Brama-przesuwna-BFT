"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
_CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
_CARD_VERSION = "0.1.7"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it in Lovelace, including YAML mode."""
    if not _CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: brakuje pliku karty: %s", _CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), cache_headers=False)]
        )
    except Exception as err:  # noqa: BLE001
        # The route may already exist after integration reload.
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.warning("Nie udało się udostępnić pliku karty BFT: %s", err)
            return

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        # Load the card as an extra module even if Lovelace has not initialized
        # its resource registry yet; setup is retried once HA has fully started.
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.warning(
            "Lovelace nie udostępnił jeszcze rejestru zasobów; dodano kartę BFT jako dodatkowy moduł JS."
        )
        return

    # YAML-managed Lovelace resources are read-only; inject the module through
    # the same frontend helper used by the working AtlasCube integration.
    if getattr(lovelace, "resource_mode", "storage") == "yaml":
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.info("Zarejestrowano kartę BFT jako dodatkowy moduł JS (tryb YAML).")
        return

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.warning("Nie znaleziono rejestru zasobów Lovelace dla karty BFT.")
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
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Nie udało się automatycznie dodać zasobu karty BFT: %s", err)
