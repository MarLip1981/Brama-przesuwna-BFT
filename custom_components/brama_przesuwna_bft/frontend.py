"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
CARD_VERSION = "1.12.9"
VERSIONED_CARD_URL = f"{CARD_URL}?v={CARD_VERSION}"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register its JavaScript directly with the frontend."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_frontend_setup_started"):
        return

    if not CARD_PATH.is_file():
        _LOGGER.error("Brama przesuwna BFT: dashboard card file is missing: %s", CARD_PATH)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False)]
        )
    except RuntimeError:
        # HTTP paths remain registered if the integration is reloaded without restart.
        _LOGGER.debug("Brama przesuwna BFT card path is already registered")

    try:
        # Register directly with the frontend; do not depend on Lovelace storage resources.
        add_extra_js_url(hass, VERSIONED_CARD_URL)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Brama przesuwna BFT: failed to register dashboard card JavaScript")
        return

    domain_data["_frontend_setup_started"] = True
    _LOGGER.info("Brama przesuwna BFT: dashboard card frontend registration completed")
