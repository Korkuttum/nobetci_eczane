"""DataUpdateCoordinator for Nöbetçi Eczane - Akıllı güncelleme algoritması."""
import logging
import hashlib
import json
from datetime import datetime, timedelta
import asyncio
import async_timeout

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    API_URL,
    NOSYAPI_UPDATE_TIMES,
    CONF_LAST_SUCCESS_HOUR,
)

_LOGGER = logging.getLogger(__name__)


def slugify_tr(text: str) -> str:
    """Türkçe karakterleri slug formatına çevir."""
    replacements = {
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.lower().replace(" ", "-")


def map_pharmacy(raw: dict) -> dict:
    """NosyAPI response alanlarını component formatına çevir."""
    lat = raw.get("latitude")
    lon = raw.get("longitude")
    loc = f"{lat},{lon}" if lat and lon else ""
    return {
        "name": raw.get("pharmacyName", ""),
        "address": raw.get("address", ""),
        "phone": raw.get("phone", ""),
        "dist": raw.get("district", ""),
        "loc": loc,
    }


def hash_pharmacy_list(pharmacies: list) -> str:
    """Eczane listesini hash'le — değişim tespiti için."""
    names = sorted([p.get("name", "") for p in pharmacies])
    return hashlib.md5(json.dumps(names).encode()).hexdigest()


def get_update_times_today() -> list[datetime]:
    """Bugünün güncelleme zamanlarını datetime olarak döndür."""
    now = dt_util.now()
    times = []
    for t in NOSYAPI_UPDATE_TIMES:
        hour, minute = map(int, t.split(":"))
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        times.append(scheduled)
    return times


def is_calibration_day() -> bool:
    """
    Haftada bir gün (Pazartesi) zıplama mantığını devre dışı bırak.

    Amaç: API'nin gerçek güncelleme saati zamanla kayabilir (ör. 10:05 -> 11:05).
    Zıplama aktifken sistem sadece bilinen saati (last_success_hour) kontrol
    ettiği için daha erken bir saatte oluşan değişikliği asla göremez.
    Kalibrasyon gününde tüm saatler sırayla denenerek gerçek saat yeniden tespit edilir.
    """
    return dt_util.now().weekday() == 0  # 0 = Pazartesi


def get_next_schedule(last_success_hour: str | None) -> datetime | None:
    """
    Bir sonraki kontrol zamanını hesapla.
    
    Algoritma:
    - Her gün 09:05'te başla (zorunlu ilk kontrol)
    - 09:05'te değişmediyse last_success_hour'a zıpla
    - Oradan sırayla devam et, değişince dur
    - Ertesi sabah 09:05'te tekrar başla
    """
    now = dt_util.now()
    times = get_update_times_today()
    first_time = times[0]  # 09:05

    # Eğer bugün henüz 09:05 olmadıysa, bugünkü 09:05'i döndür
    if now < first_time:
        return first_time

    # Bugünkü zamanlardan geçmemişleri bul
    upcoming = [t for t in times if t > now]

    if not upcoming:
        # Bugün tüm saatler geçti, yarın 09:05
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(
            hour=int(NOSYAPI_UPDATE_TIMES[0].split(":")[0]),
            minute=int(NOSYAPI_UPDATE_TIMES[0].split(":")[1]),
            second=0, microsecond=0
        )

    # Şu an 09:05-09:05 arasındayız (yani 09:05 geçti ama henüz sonuç yok)
    # last_success_hour varsa ve şu anki saatten büyükse ona zıpla
    if last_success_hour:
        target_hour, target_minute = map(int, last_success_hour.split(":"))
        target_today = now.replace(
            hour=target_hour, minute=target_minute, second=0, microsecond=0
        )
        # Hedef saat henüz gelmediyse ve upcoming listesinde varsa ona zıpla
        if target_today in upcoming:
            return target_today
        # Hedef saatten sonraki ilk zamanı bul
        after_target = [t for t in upcoming if t >= target_today]
        if after_target:
            return after_target[0]

    # last_success_hour yoksa veya bulunamadıysa, sıradaki zamana geç
    return upcoming[0]


class NobetciEczaneCoordinator(DataUpdateCoordinator):
    """Akıllı zamanlama ile NosyAPI'den veri çeken koordinatör."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        city: str,
        district: str | None,
        api_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Nöbetçi Eczane {city}/{district if district else 'Tümü'}",
            # update_interval yok — manuel zamanlama kullanıyoruz
        )
        self.city = city
        self.district = district
        self.api_key = api_key
        self.config_entry = config_entry
        self.session = async_get_clientsession(hass)
        self._previous_hash: str | None = None
        self._unsub_timer = None
        self._last_success_hour: str | None = config_entry.data.get(CONF_LAST_SUCCESS_HOUR)

    async def async_start_smart_scheduler(self) -> None:
        """İlk zamanlamayı başlat."""
        await self._schedule_next()

    async def _schedule_next(self) -> None:
        """Bir sonraki kontrol zamanını hesaplayıp planla."""
        # Kalibrasyon gününde zıplamayı iptal et — sırayla tüm saatler denenir
        effective_last_success = (
            None if is_calibration_day() else self._last_success_hour
        )
        next_time = get_next_schedule(effective_last_success)
        if next_time is None:
            return

        if is_calibration_day() and self._last_success_hour is not None:
            _LOGGER.debug(
                "Nöbetçi Eczane %s/%s — kalibrasyon günü, zıplama iptal",
                self.city, self.district
            )

        _LOGGER.debug(
            "Nöbetçi Eczane %s/%s — sonraki kontrol: %s",
            self.city, self.district, next_time.strftime("%H:%M")
        )

        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

        @callback
        def _fire(_now):
            self.hass.async_create_task(self._scheduled_update())

        self._unsub_timer = async_track_point_in_time(
            self.hass, _fire, next_time
        )

    async def _scheduled_update(self) -> None:
        """Zamanlayıcı tetiklendiğinde çalışır."""
        now = dt_util.now()
        current_time_str = now.strftime("%H:%M")
        times_today = [t.strftime("%H:%M") for t in get_update_times_today()]
        is_first_slot = (current_time_str == times_today[0] if times_today else False)

        new_data = await self._fetch_data()

        if new_data is None:
            # Hata durumunda bir sonraki slota geç
            _LOGGER.warning("Veri alınamadı, bir sonraki slota geçiliyor.")
            await self._schedule_next()
            return

        new_hash = hash_pharmacy_list(new_data)

        if self._previous_hash is None or new_hash != self._previous_hash:
            # Veri değişti veya ilk yükleme
            _LOGGER.info(
                "Nöbetçi eczane verisi güncellendi: %s/%s @ %s",
                self.city, self.district, current_time_str
            )
            self._previous_hash = new_hash
            self.async_set_updated_data(new_data)

            if not is_first_slot:
                # İlk slot değilse başarılı saati kaydet
                await self._save_last_success_hour(current_time_str)

            # Değişti → bugün için bitti, yarın 09:05'e planla
            self._last_success_hour = current_time_str if not is_first_slot else self._last_success_hour
            await self._schedule_next_day()
        else:
            # Veri değişmedi
            _LOGGER.debug(
                "Veri değişmedi: %s/%s @ %s — sonraki slota geçiliyor",
                self.city, self.district, current_time_str
            )
            await self._schedule_next()

    async def _schedule_next_day(self) -> None:
        """Yarın 09:05'e planla."""
        now = dt_util.now()
        tomorrow = now + timedelta(days=1)
        next_time = tomorrow.replace(
            hour=int(NOSYAPI_UPDATE_TIMES[0].split(":")[0]),
            minute=int(NOSYAPI_UPDATE_TIMES[0].split(":")[1]),
            second=0, microsecond=0
        )

        _LOGGER.debug(
            "Nöbetçi Eczane %s/%s — yarın kontrol: %s",
            self.city, self.district, next_time.strftime("%Y-%m-%d %H:%M")
        )

        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

        @callback
        def _fire(_now):
            self.hass.async_create_task(self._scheduled_update())

        self._unsub_timer = async_track_point_in_time(
            self.hass, _fire, next_time
        )

    async def _save_last_success_hour(self, hour_str: str) -> None:
        """Başarılı saati config_entry'e kaydet."""
        self._last_success_hour = hour_str
        new_data = {**self.config_entry.data, CONF_LAST_SUCCESS_HOUR: hour_str}
        self.hass.config_entries.async_update_entry(
            self.config_entry, data=new_data
        )
        _LOGGER.debug("Son başarılı saat kaydedildi: %s", hour_str)

    async def _fetch_data(self) -> list | None:
        """NosyAPI'den veri çek."""
        city_slug = slugify_tr(self.city)
        district_slug = slugify_tr(self.district) if self.district else None

        params = {"apiKey": self.api_key, "city": city_slug}
        if district_slug:
            params["district"] = district_slug

        try:
            async with async_timeout.timeout(10):
                async with self.session.get(API_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_list = data.get("data", [])
                        if not raw_list:
                            _LOGGER.warning(
                                "Boş veri döndü: %s/%s", self.city, self.district
                            )
                            return []
                        return [map_pharmacy(p) for p in raw_list]
                    else:
                        _LOGGER.error(
                            "API hatası %s/%s: %s", self.city, self.district, resp.status
                        )
                        return None
        except asyncio.TimeoutError:
            _LOGGER.error("Zaman aşımı: %s/%s", self.city, self.district)
        except Exception as err:
            _LOGGER.error("Hata: %s/%s — %s", self.city, self.district, str(err))
        return None

    async def _async_update_data(self):
        """DataUpdateCoordinator zorunlu override — manuel zamanlama kullandığımız için boş."""
        return self.data

    def async_stop(self) -> None:
        """Zamanlayıcıyı durdur."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
