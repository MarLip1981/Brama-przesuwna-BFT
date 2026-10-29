"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

from .const import PLATFORMS
from .frontend import async_setup_frontend


async def _async_frontend_after_start(hass: HomeAssistant, event: Event) -> None:
    """Retry registration after Lovelace and frontend initialization."""
    await async_setup_frontend(hass)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the dashboard card and retry after Home Assistant starts."""
    await async_setup_frontend(hass)
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STARTED,
        lambda event: hass.async_create_task(_async_frontend_after_start(hass, event)),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up entities and register the frontend card."""
    await async_setup_frontend(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
