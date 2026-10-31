"""Automatic frontend module registration for the BFT dashboard card."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
CARD_PATH = Path(__file__).parent / "www" / "brama-przesuwna-bft-card.js"
CARD_URL = "/brama_przesuwna_bft/brama-przesuwna-bft-card.js"
CARD_VERSION = "1.12.8"
VERSIONED_CARD_URL = f"{CARD_URL}?v={CARD_VERSION}"
_RESOURCE_MARKER = "_lovelace_resource_registered"


async def _async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Register the card as a Lovelace resource when storage mode is available.

    Lovelace resources load after the frontend's custom-element registry setup.
    This avoids the startup race affecting modules injected with add_extra_js_url.
    """
    lovelace_data: Any = hass.data.get("lovelace")
    resources = getattr(lovelace_data, "resources", None)
    if resources is None:
        return False

    try:
        if not getattr(resources, "loaded", False):
            await resources.async_load()
            resources.loaded = True

        for resource in resources.async_items():
            url = str(resource.get("url", ""))
            if url.split("?", 1)[0] == CARD_URL:
                if url != VERSIONED_CARD_URL:
                    resource_id = resource.get("id")
                    update_item = getattr(resources, "async_update_item", None)
                    if resource_id is not None and callable(update_item):
                        # The ID is managed by Home Assistant; update only the URL.
                        await update_item(resource_id, {"url": VERSIONED_CARD_URL})
                return True

        create_item = getattr(resources, "async_create_item", None)
        if not callable(create_item):
            return False
        await create_item({"res_type": "module", "url": VERSIONED_CARD_URL})
        _LOGGER.info("Brama przesuwna BFT: dashboard card registered as a Lovelace resource")
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Brama przesuwna BFT: could not register the Lovelace card resource")
        return False


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the card and register it with the frontend."""
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

    # Prefer Lovelace resources: they load after the frontend registry is initialized.
    resource_registered = await _async_register_lovelace_resource(hass)
    if not resource_registered:
        try:
            add_extra_js_url(hass, VERSIONED_CARD_URL)
            _LOGGER.warning(
                "Brama przesuwna BFT: using frontend extra-module fallback; "
                "automatic card registration may be affected by frontend startup timing"
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Brama przesuwna BFT: failed to register dashboard card JavaScript")
            return

    domain_data["_frontend_setup_started"] = True
    domain_data[_RESOURCE_MARKER] = resource_registered
    _LOGGER.info("Brama przesuwna BFT: dashboard card frontend registration completed")
