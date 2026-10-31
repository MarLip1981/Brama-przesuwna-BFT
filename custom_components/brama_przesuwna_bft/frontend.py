"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
CARD_VERSION = "1.13.0"
VERSIONED_CARD_URL = f"{CARD_URL}?v={CARD_VERSION}"


async def _async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Register the card as a dashboard resource in storage mode."""
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return False

    # YAML resources are read-only. In that mode we use the frontend-module
    # fallback; the JavaScript waits for HA's final custom-elements registry.
    if getattr(lovelace, "resource_mode", "storage") == "yaml":
        add_extra_js_url(hass, VERSIONED_CARD_URL)
        _LOGGER.info(
            "Brama przesuwna BFT: card registered as a deferred frontend module "
            "because Lovelace resources are managed in YAML mode"
        )
        return True

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        return False

    try:
        if not getattr(resources, "loaded", False):
            await resources.async_load()
            resources.loaded = True

        matching = [
            item for item in resources.async_items()
            if str(item.get("url", "")).split("?", 1)[0] == CARD_URL
        ]

        if matching:
            primary = matching[0]
            if primary.get("url") != VERSIONED_CARD_URL:
                await resources.async_update_item(
                    primary["id"], {"url": VERSIONED_CARD_URL}
                )
            for duplicate in matching[1:]:
                await resources.async_delete_item(duplicate["id"])
            _LOGGER.info(
                "Brama przesuwna BFT: Lovelace resource is registered: %s",
                VERSIONED_CARD_URL,
            )
            return True

        await resources.async_create_item(
            {"res_type": "module", "url": VERSIONED_CARD_URL}
        )
        _LOGGER.info(
            "Brama przesuwna BFT: added Lovelace resource: %s",
            VERSIONED_CARD_URL,
        )
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "Brama przesuwna BFT: could not register the Lovelace card resource"
        )
        return False


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it using the dashboard resource mechanism."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_frontend_setup_started"):
        return

    if not CARD_PATH.is_file():
        _LOGGER.error(
            "Brama przesuwna BFT: dashboard card file is missing: %s", CARD_PATH
        )
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False)]
        )
    except RuntimeError:
        # HTTP paths remain registered if the integration is reloaded without restart.
        _LOGGER.debug("Brama przesuwna BFT card path is already registered")

    if not await _async_register_lovelace_resource(hass):
        # This is only a fallback for unusual startup states where Lovelace
        # has not exposed its resource collection yet.
        try:
            add_extra_js_url(hass, VERSIONED_CARD_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "Brama przesuwna BFT: failed to register dashboard card JavaScript"
            )
            return

    domain_data["_frontend_setup_started"] = True
    _LOGGER.info("Brama przesuwna BFT: dashboard card frontend registration completed")
