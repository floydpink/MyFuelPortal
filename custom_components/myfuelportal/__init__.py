"""MyFuelPortal integration."""
import logging

from .const import DOMAIN, CONF_PROVIDER
from .coordinator import MyFuelPortalCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(hass, entry):
    coordinator = MyFuelPortalCoordinator(
        hass,
        entry.data[CONF_PROVIDER],
        entry.data["username"],
        entry.data["password"],
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok
