"""Constants for the Nöbetçi Eczane integration."""
from datetime import timedelta

DOMAIN = "nobetci_eczane"

CONF_CITY = "city"
CONF_DISTRICT = "district"
CONF_API_KEY = "api_key"
CONF_LAST_SUCCESS_HOUR = "last_success_hour"

DEFAULT_NAME = "Nöbetçi Eczane"
DEFAULT_ICON = "mdi:medical-bag"

API_URL = "https://www.nosyapi.com/apiv2/service/pharmacies-on-duty"
API_HEADERS_CONTENT_TYPE = "application/json"

ATTRIBUTION = "Data provided by NosyAPI"

# NosyAPI güncelleme saatleri + 5 dakika
NOSYAPI_UPDATE_TIMES = ["09:05", "10:05", "11:05", "13:05", "15:05", "17:05", "19:35"]

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
