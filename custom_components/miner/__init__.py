"""The Miner integration."""
from __future__ import annotations


try:
    import pyasic
except ImportError:
    from .patch import install_package
    from .const import PYASIC_VERSION

    install_package(f"pyasic=={PYASIC_VERSION}")
    import pyasic

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta, datetime, time
from zoneinfo import ZoneInfo

from .const import (
    AMBIENT_TEMP_RESUME_F,
    AMBIENT_TEMP_STOP_F,
    CONF_IP,
    DOMAIN,
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

        if eastern.weekday() < 5 and time(14, 0) <= eastern.time() < time(21, 0):
            if m_coordinator.data.get("is_mining"):
                await miner.stop_mining()
            return
        state = hass.states.get("sensor.econet_hpwh_ambient_temperature")
        if not state or state.state in ("unknown", "unavailable"):
            return
        try:
            ambient = float(state.state)
        except ValueError:
            return
        if ambient < AMBIENT_TEMP_RESUME_F:
            await miner.resume_mining()
        elif ambient > AMBIENT_TEMP_STOP_F:
            await miner.stop_mining()

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
