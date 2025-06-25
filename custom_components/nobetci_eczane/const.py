"""Constants for the Nöbetçi Eczane integration."""
from datetime import timedelta

DOMAIN = "nobetci_eczane"

CONF_CITY = "city"
CONF_DISTRICT = "district"
CONF_API_KEY = "api_key"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_UPDATE_HOUR = "update_hour"

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)
DEFAULT_UPDATE_HOUR = 8

DEFAULT_NAME = "Nöbetçi Eczane"
DEFAULT_ICON = "mdi:medical-bag"

API_URL = "https://api.collectapi.com/health/dutyPharmacy"
API_HEADERS_CONTENT_TYPE = "application/json"

ATTRIBUTION = "Data provided by CollectAPI"

ATTR_NAME = "name"
ATTR_ADDRESS = "address"
ATTR_PHONE = "phone"
ATTR_DISTRICT = "dist"
ATTR_LOCATION = "loc"
ATTR_PHARMACY_NUMBER = "pharmacy_number"
ATTR_LAST_UPDATE = "last_update"
ATTR_MAPS_URL = "maps_url"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"