"""The Nöbetçi Eczane integration."""
import logging
import hashlib
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_CITY, CONF_DISTRICT, CONF_API_KEY
from .coordinator import NobetciEczaneCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nöbetçi Eczane from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = NobetciEczaneCoordinator(
        hass=hass,
        config_entry=entry,
        city=entry.data[CONF_CITY],
        district=entry.data.get(CONF_DISTRICT),
        api_key=entry.data[CONF_API_KEY],
    )

    # İlk veriyi çek ve koordinatöre set et
    initial_data = await coordinator._fetch_data()
    if initial_data is not None:
        coordinator.async_set_updated_data(initial_data)
        names = sorted([p.get("name", "") for p in initial_data])
        coordinator._previous_hash = hashlib.md5(json.dumps(names).encode()).hexdigest()

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Akıllı zamanlayıcıyı başlat
    await coordinator.async_start_smart_scheduler()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: NobetciEczaneCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
