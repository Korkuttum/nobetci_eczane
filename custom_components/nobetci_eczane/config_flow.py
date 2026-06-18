"""Config flow for Nöbetçi Eczane integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import json
import os
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_DISTRICT,
    CONF_API_KEY,
    API_URL,
)


async def async_load_cities_data(hass) -> dict:
    """Load cities and districts data from JSON file — executor'da çalıştır."""
    def _load():
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(current_dir, 'il-ilce.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {city['il_adi']: [ilce['ilce_adi'] for ilce in city['ilceler']] for city in data}

    try:
        return await hass.async_add_executor_job(_load)
    except Exception as e:
        print(f"JSON dosyası yüklenemedi: {e}")
        return {}


class NobetciEczaneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nöbetçi Eczane."""

    VERSION = 1

    def __init__(self):
        """Initialize flow."""
        self.cities_data = {}
        self.selected_city = None
        self._api_key = None

    async def _test_api(self, api_key: str) -> bool:
        """Test NosyAPI connection."""
        session = async_get_clientsession(self.hass)
        params = {"apiKey": api_key, "city": "istanbul"}
        try:
            async with session.get(API_URL, params=params) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status != 200:
                    raise CannotConnect
                data = await response.json()
                if data.get("status") != "success":
                    raise InvalidAuth
                return True
        except aiohttp.ClientError:
            raise CannotConnect
        except (InvalidAuth, CannotConnect):
            raise
        except Exception:
            raise CannotConnect

    async def async_step_user(self, user_input=None):
        """Handle the initial step — API key."""
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
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
            description_placeholders={
                "api_url": "https://www.nosyapi.com/api/nobetci-eczane"
            },
        )

    async def async_step_location(self, user_input=None):
        """Handle the city selection step."""
        errors = {}

        # İl listesini async olarak yükle
        if not self.cities_data:
            self.cities_data = await async_load_cities_data(self.hass)

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

            await self.async_set_unique_id(f"{self.selected_city}_{district}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Nöbetçi Eczane - {self.selected_city}/{district}",
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_CITY: self.selected_city,
                    CONF_DISTRICT: district,
                },
            )

        return self.async_show_form(
            step_id="district",
            data_schema=vol.Schema({
                vol.Required(CONF_DISTRICT): vol.In(self.cities_data[self.selected_city]),
            }),
            errors=errors,
            description_placeholders={"city": self.selected_city},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Options flow yok."""
        return None


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
