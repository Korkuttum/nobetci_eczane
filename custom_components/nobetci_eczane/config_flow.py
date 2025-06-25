"""Config flow for Nöbetçi Eczane integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import json
import os
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_DISTRICT,
    CONF_API_KEY,
    CONF_UPDATE_HOUR,
    DEFAULT_UPDATE_HOUR,
    API_URL
)

def load_cities_data():
    """Load cities and districts data from JSON file."""
    try:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(current_dir, 'il-ilce.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # İl listesini oluştur
        cities = {city['il_adi']: [ilce['ilce_adi'] for ilce in city['ilceler']] for city in data}
        return cities
    except Exception as e:
        print(f"JSON dosyası yüklenemedi: {e}")
        return {}

def format_hour(hour):
    """Format hour as HH:00."""
    return f"{hour:02d}:00"

def get_hours_list():
    """Get list of hours in HH:00 format."""
    return [format_hour(h) for h in range(24)]

class NobetciEczaneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nöbetçi Eczane."""

    VERSION = 1
    
    def __init__(self):
        """Initialize flow."""
        self.cities_data = load_cities_data()
        self.selected_city = None
        self._api_key = None

    async def _test_api(self, api_key: str) -> bool:
        """Test API connection."""
        session = async_get_clientsession(self.hass)
        headers = {
            "content-type": "application/json",
            "authorization": f"apikey {api_key}"
        }
        params = {
            "il": "istanbul"
        }

        try:
            async with session.get(
                API_URL,
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status != 200:
                    raise CannotConnect
                await response.json()
                return True
        except aiohttp.ClientError:
            raise CannotConnect
        except Exception:
            raise

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                await self._test_api(user_input[CONF_API_KEY])
                self._api_key = user_input[CONF_API_KEY]
                return await self.async_step_location()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
            description_placeholders={
                "api_url": "https://collectapi.com/tr/api/health/nobetci-eczane-api"
            },
        )

    async def async_step_location(self, user_input=None):
        """Handle the city selection step."""
        errors = {}

        if user_input is not None:
            self.selected_city = user_input[CONF_CITY]
            return await self.async_step_district()

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema({
                vol.Required(CONF_CITY): vol.In(list(self.cities_data.keys())),
            }),
            errors=errors,
        )

    async def async_step_district(self, user_input=None):
        """Handle the district selection step."""
        errors = {}

        if user_input is not None:
            district = user_input[CONF_DISTRICT]
            update_hour = int(user_input[CONF_UPDATE_HOUR].split(":")[0])

            await self.async_set_unique_id(f"{self.selected_city}_{district}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Nöbetçi Eczane - {self.selected_city}/{district}",
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_CITY: self.selected_city,
                    CONF_DISTRICT: district,
                    CONF_UPDATE_HOUR: update_hour
                },
            )

        return self.async_show_form(
            step_id="district",
            data_schema=vol.Schema({
                vol.Required(CONF_DISTRICT): vol.In(self.cities_data[self.selected_city]),
                vol.Required(CONF_UPDATE_HOUR, default=format_hour(DEFAULT_UPDATE_HOUR)): vol.In(get_hours_list()),
            }),
            errors=errors,
            description_placeholders={"city": self.selected_city},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Nobetci Eczane."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            update_hour = int(user_input[CONF_UPDATE_HOUR].split(":")[0])
            return self.async_create_entry(
                title="",
                data={CONF_UPDATE_HOUR: update_hour},
            )

        current_hour = self.config_entry.data.get(CONF_UPDATE_HOUR, DEFAULT_UPDATE_HOUR)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_UPDATE_HOUR,
                    default=format_hour(current_hour)
                ): vol.In(get_hours_list()),
            }),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""