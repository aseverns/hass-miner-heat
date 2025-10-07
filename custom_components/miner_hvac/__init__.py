"""The Miner HVAC integration."""
from __future__ import annotations


try:
    import pyasic
except ImportError:
    from .patch import install_package
    from .const import PYASIC_VERSION

    install_package(f"pyasic=={PYASIC_VERSION}")
    import pyasic

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_IP,
    DEFAULT_HEAT_SETPOINT_F,
    DOMAIN,
    HEAT_SETPOINT_ENTITY_ID,
    LIVING_ROOM_TEMPERATURE_SENSOR,
    LIVING_ROOM_THERMOSTAT,
    NEST_FAN_MODE_AUTO,
    NEST_FAN_MODE_ON,
)
from .coordinator import MinerCoordinator
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Miner from a config entry."""

    miner_ip = config_entry.data[CONF_IP]
    miner = await pyasic.get_miner(miner_ip)

    if miner is None:
        raise ConfigEntryNotReady("Miner could not be found.")

    m_coordinator = MinerCoordinator(hass, config_entry)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = m_coordinator

    await m_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    await async_setup_services(hass)

    async def _curtail_check(now):
        eastern = datetime.now(ZoneInfo("US/Eastern"))
        miner = m_coordinator.miner
        if miner is None:
            return

        miner_is_running = bool(m_coordinator.data.get("is_mining"))

        async def _set_fan_mode(target_mode: str) -> None:
            thermostat_state = hass.states.get(LIVING_ROOM_THERMOSTAT)
            if (
                thermostat_state
                and thermostat_state.attributes.get("fan_mode") == target_mode
            ):
                return
            await hass.services.async_call(
                "climate",
                "set_fan_mode",
                {
                    "entity_id": LIVING_ROOM_THERMOSTAT,
                    "fan_mode": target_mode,
                },
                blocking=True,
            )

        if eastern.weekday() < 5 and time(14, 0) <= eastern.time() < time(21, 0):
            if miner_is_running:
                await miner.stop_mining()
                await _set_fan_mode(NEST_FAN_MODE_ON)
            else:
                await _set_fan_mode(NEST_FAN_MODE_AUTO)
            return

        state = hass.states.get(LIVING_ROOM_TEMPERATURE_SENSOR)
        if not state or state.state in ("unknown", "unavailable"):
            if miner_is_running:
                await _set_fan_mode(NEST_FAN_MODE_ON)
            return
        try:
            ambient = float(state.state)
        except ValueError:
            if miner_is_running:
                await _set_fan_mode(NEST_FAN_MODE_ON)
            return

        setpoint_state = hass.states.get(HEAT_SETPOINT_ENTITY_ID)
        try:
            setpoint = (
                float(setpoint_state.state)
                if setpoint_state
                and setpoint_state.state not in ("unknown", "unavailable")
                else DEFAULT_HEAT_SETPOINT_F
            )
        except (TypeError, ValueError):
            setpoint = DEFAULT_HEAT_SETPOINT_F

        if ambient < setpoint:
            await miner.resume_mining()
            await _set_fan_mode(NEST_FAN_MODE_ON)
        else:
            await miner.stop_mining()
            if miner_is_running:
                await _set_fan_mode(NEST_FAN_MODE_ON)
            else:
                await _set_fan_mode(NEST_FAN_MODE_AUTO)

    unsub = async_track_time_interval(hass, _curtail_check, timedelta(minutes=5))
    config_entry.async_on_unload(unsub)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
