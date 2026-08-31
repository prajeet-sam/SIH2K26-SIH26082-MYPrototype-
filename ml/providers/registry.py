from __future__ import annotations

from ml.config.settings import Settings
from ml.providers.base import AirQualityProvider, WeatherProvider
from ml.providers.demo import DemoAirQualityProvider, DemoWeatherProvider
from ml.providers.open_meteo import OpenMeteoWeatherProvider
from ml.providers.open_meteo_air import OpenMeteoAirQualityProvider


def build_air_quality_providers(settings: Settings) -> list[AirQualityProvider]:
    if settings.demo_mode:
        return [DemoAirQualityProvider()]
    providers: list[AirQualityProvider] = []
    if settings.data_gov_in_api_key:
        from ml.providers.cpcb import CpcbProvider

        providers.append(CpcbProvider(settings))
    if settings.openaq_api_key:
        from ml.providers.openaq import OpenAqProvider

        providers.append(OpenAqProvider(settings))
    providers.append(OpenMeteoAirQualityProvider(settings))
    if settings.waqi_api_token:
        from ml.providers.waqi import WaqiProvider

        providers.append(WaqiProvider(settings))
    return providers


def build_weather_providers(settings: Settings) -> list[WeatherProvider]:
    if settings.demo_mode:
        return [DemoWeatherProvider()]
    return [OpenMeteoWeatherProvider(settings)]
