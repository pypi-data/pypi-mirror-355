

OPENMETEO = 'openmeteo'
WEATHER_UNDERGROUND = 'weather_underground'
WEATHER_API = 'weather_api'
TMD = 'tmd'

_historical_sources = [
    OPENMETEO,
    WEATHER_API,
    WEATHER_UNDERGROUND,
]

_forecast_sources = [
    OPENMETEO,
    WEATHER_API,
    TMD,
]

def get_historical_sources() -> list[str]:
    return _historical_sources

def get_forecast_sources() -> list[str]:
    return _forecast_sources
