"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .frontend import async_setup_frontend


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the dashboard card independently of the config entry."""
    await async_setup_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration entities and make a second frontend registration attempt."""
    await async_setup_frontend(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
