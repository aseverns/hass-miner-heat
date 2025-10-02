"""The Miner component services."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.core import ServiceCall
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN
from .const import SERVICE_REBOOT
from .const import SERVICE_RESTART_BACKEND
from .const import SERVICE_CURTAIL_WAKEUP
from .const import SERVICE_CURTAIL_SLEEP

LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Service handler setup."""

    async def get_miners(call: ServiceCall):
        hass_devices = hass.data[DOMAIN]

        miner_ids = call.data[CONF_DEVICE_ID]

        if not miner_ids:
            return

        registry = async_get_device_registry(hass)

        return await asyncio.gather(
            *(
                [
                    hass_devices[registry.async_get(d).primary_config_entry].get_miner()
                    for d in miner_ids
                ]
            )
        )

    async def reboot(call: ServiceCall) -> None:
        miners = await get_miners(call)
        if len(miners) > 0:
            await asyncio.gather(*[miner.reboot() for miner in miners])

    hass.services.async_register(DOMAIN, SERVICE_REBOOT, reboot)

    async def restart_backend(call: ServiceCall) -> None:
        miners = await get_miners(call)
        if len(miners) > 0:
            await asyncio.gather(*[miner.restart_backend() for miner in miners])

    hass.services.async_register(DOMAIN, SERVICE_RESTART_BACKEND, restart_backend)

    async def curtail_wakeup(call: ServiceCall) -> None:
        miners = await get_miners(call)
        if len(miners) > 0:
            await asyncio.gather(*[miner.resume_mining() for miner in miners])

    hass.services.async_register(DOMAIN, SERVICE_CURTAIL_WAKEUP, curtail_wakeup)

    async def curtail_sleep(call: ServiceCall) -> None:
        miners = await get_miners(call)
        if len(miners) > 0:
            await asyncio.gather(*[miner.stop_mining() for miner in miners])

    hass.services.async_register(DOMAIN, SERVICE_CURTAIL_SLEEP, curtail_sleep)
