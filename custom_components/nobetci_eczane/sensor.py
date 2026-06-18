"""Sensor platform for Nöbetçi Eczane integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_DISTRICT,
    ATTRIBUTION,
    ATTR_NAME,
    ATTR_ADDRESS,
    ATTR_PHONE,
    ATTR_DISTRICT,
    ATTR_PHARMACY_NUMBER,
    ATTR_LAST_UPDATE,
    ATTR_MAPS_URL,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from .coordinator import NobetciEczaneCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = [
    SensorEntityDescription(
        key="name",
        name="İsim",
        icon="mdi:medical-bag",
        device_class=None,
        state_class=None,
    ),
    SensorEntityDescription(
        key="address",
        name="Adres",
        icon="mdi:map-marker",
        device_class=None,
        state_class=None,
    ),
    SensorEntityDescription(
        key="phone",
        name="Telefon",
        icon="mdi:phone",
        device_class=None,
        state_class=None,
    ),
    SensorEntityDescription(
        key="dist",
        name="Bölge",
        icon="mdi:city",
        device_class=None,
        state_class=None,
    ),
    SensorEntityDescription(
        key="loc",
        name="Konum",
        icon="mdi:crosshairs-gps",
        device_class=None,
        state_class=None,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nöbetçi Eczane sensors."""
    coordinator: NobetciEczaneCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    city = config_entry.data[CONF_CITY]
    district = config_entry.data.get(CONF_DISTRICT)

    sensors = []
    if coordinator.data:
        for idx, _ in enumerate(coordinator.data):
            for description in SENSOR_TYPES:
                sensors.append(
                    NobetciEczaneSensor(
                        coordinator=coordinator,
                        description=description,
                        idx=idx,
                        city=city,
                        district=district,
                        config_entry=config_entry,
                    )
                )

    async_add_entities(sensors, True)


class NobetciEczaneSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Nöbetçi Eczane sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: NobetciEczaneCoordinator,
        description: SensorEntityDescription,
        idx: int,
        city: str,
        district: str | None,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.idx = idx
        self._city = city
        self._district = district

        base_name = f"{city}_{district if district else 'all'}"
        self._attr_unique_id = f"nobetci_eczane_{base_name}_{idx+1}_{description.key}"
        self._attr_name = f"{idx+1}. Eczane {description.name}"
        self._attr_icon = description.icon

        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{city}_{district if district else 'all'}")},
            "name": f"Nöbetçi Eczaneler - {city}/{district if district else 'Tümü'}",
            "manufacturer": "NosyAPI",
            "model": "Nöbetçi Eczane",
            "sw_version": "1.2.0",
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        try:
            if (
                self.coordinator.data
                and len(self.coordinator.data) > self.idx
                and self.coordinator.data[self.idx]
            ):
                value = self.coordinator.data[self.idx].get(self.entity_description.key)
                if self.entity_description.key == "loc" and value:
                    return f"https://www.google.com/maps/search/?api=1&query={value}"
                return value if value else "Bilgi yok"
            return "Veri yok"
        except Exception as err:
            _LOGGER.error("Sensör değeri hatası %s: %s", self.entity_id, str(err))
            return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        try:
            if (
                self.coordinator.data
                and len(self.coordinator.data) > self.idx
                and self.coordinator.data[self.idx]
            ):
                pharmacy = self.coordinator.data[self.idx]
                location = pharmacy.get("loc", "")

                attributes = {
                    ATTR_LAST_UPDATE: dt.now().isoformat(),
                    ATTR_PHARMACY_NUMBER: self.idx + 1,
                    CONF_CITY: self._city,
                    CONF_DISTRICT: self._district if self._district else "Tümü",
                    ATTR_NAME: pharmacy.get("name", ""),
                    ATTR_ADDRESS: pharmacy.get("address", ""),
                    ATTR_PHONE: pharmacy.get("phone", ""),
                    ATTR_DISTRICT: pharmacy.get("dist", ""),
                }

                if location:
                    attributes[ATTR_MAPS_URL] = f"https://www.google.com/maps/search/?api=1&query={location}"
                    try:
                        lat, lon = location.split(",")
                        attributes[ATTR_LATITUDE] = float(lat)
                        attributes[ATTR_LONGITUDE] = float(lon)
                    except (ValueError, AttributeError):
                        pass

                return attributes
            return {}
        except Exception as err:
            _LOGGER.error("Sensör attribute hatası %s: %s", self.entity_id, str(err))
            return {}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and bool(self.coordinator.data)
            and len(self.coordinator.data) > self.idx
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        super()._handle_coordinator_update()
