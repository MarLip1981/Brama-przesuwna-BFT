"""Home Assistant integration for the BFT sliding gate project."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DEFAULT_NOTIFY_TARGET,
    GATE_STATUS_ENTITY,
    OPTION_NOTIFY_CLOSED,
    OPTION_NOTIFY_OPEN,
    OPTION_NOTIFY_TARGETS,
    PLATFORMS,
)
from .frontend import async_setup_frontend

_LOGGER = logging.getLogger(__name__)


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


async def _async_gate_state_changed(hass: HomeAssistant, entry: ConfigEntry, event: Event) -> None:
    """Notify selected targets when the gate reaches a configured final state."""
    new_state = event.data.get("new_state")
    if new_state is None:
        return

    configured_entities = entry.options.get(
        "esphome_entities", entry.data.get("esphome_entities", {})
    )
    status_entity = configured_entities.get("status", GATE_STATUS_ENTITY)
    if event.data.get("entity_id") != status_entity:
        return

    state = new_state.state
    if state == "Otwarta":
        enabled = entry.options.get(
            OPTION_NOTIFY_OPEN, entry.data.get(OPTION_NOTIFY_OPEN, False)
        )
        message = "Brama wjazdowa jest otwarta."
    elif state == "Zamknięta":
        enabled = entry.options.get(
            OPTION_NOTIFY_CLOSED, entry.data.get(OPTION_NOTIFY_CLOSED, False)
        )
        message = "Brama wjazdowa jest zamknięta."
    else:
        return

    if not enabled:
        return

    await asyncio.sleep(2)
    current_state = hass.states.get(status_entity)
    if current_state is None or current_state.state != state:
        return

    targets = entry.options.get(
        OPTION_NOTIFY_TARGETS,
        entry.data.get(OPTION_NOTIFY_TARGETS, [DEFAULT_NOTIFY_TARGET]),
    )
    if isinstance(targets, str):
        targets = [targets]

    for target in targets:
        if not target:
            continue
        try:
            await hass.services.async_call(
                "notify",
                target,
                {"message": message, "title": "Brama wjazdowa"},
                blocking=True,
            )
            _LOGGER.debug("Wysłano powiadomienie o stanie bramy przez notify.%s", target)
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "Nie udało się wysłać powiadomienia przez notify.%s. "
                "Sprawdź, czy ta usługa jest dostępna.",
                target,
            )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up entities, frontend card and configured notifications."""
    await async_setup_frontend(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        async_track_state_change_event(
            hass,
            [entry.options.get("esphome_entities", entry.data.get("esphome_entities", {})).get("status", GATE_STATUS_ENTITY)],
            lambda event: hass.async_create_task(
                _async_gate_state_changed(hass, entry, event)
            ),
        )
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
