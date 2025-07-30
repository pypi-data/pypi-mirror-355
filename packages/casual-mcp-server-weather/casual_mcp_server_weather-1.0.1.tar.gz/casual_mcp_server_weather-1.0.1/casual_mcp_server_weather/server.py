from typing import Annotated, Tuple
from fastmcp import FastMCP
from pydantic import Field
import requests
from .cli import start_mcp

mcp = FastMCP("Weather", instructions="Weather tools using Open-Meteo.")

location_cache: dict[str, Tuple[float, float]] = {}


def resolve_location(location: str) -> Tuple[float, float]:
    if location.lower() in location_cache:
        return location_cache[location.lower()]

    resp = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": location})
    data = resp.json()
    results = data.get("results")
    if not results:
        raise ValueError(f"Could not resolve location: {location}")

    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    location_cache[location.lower()] = (lat, lon)
    return lat, lon


weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Rain showers",
    95: "Thunderstorm"
}

uv_risk_levels = [
    (0, 3, "Low"),
    (3, 6, "Moderate"),
    (6, 8, "High"),
    (8, 11, "Very High"),
    (11, float("inf"), "Extreme")
]


def get_uv_risk(index: float) -> str:
    for low, high, level in uv_risk_levels:
        if low <= index < high:
            return level
    return "Unknown"


@mcp.tool(description="Get current temperature, wind speed, and condition for a location.")
def current_weather(
    location: Annotated[str, Field(description="City or place name")]
) -> dict:
    lat, lon = resolve_location(location)
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params = {
            "latitude": lat, 
            "longitude": lon, 
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,wind_speed_10m,wind_direction_10m,weather_code"
        },
    )
    data = resp.json().get("current", {})
    return {
        "temperature_c": data.get("temperature_2m"),
        "relative_humidity": data.get("relative_humidity_2m"),
        "windspeed_kph": data.get("wind_speed_10m"),
        "wind_direction": data.get("wind_direction_10m"),
        "precipitation": data.get("precipitation"),
        "rain": data.get("rain"),
        "condition": weather_codes.get(data.get("weather_code"), "Unknown"),
        "time": data.get("time")
    }


@mcp.tool(description="Get the daily weather forecast for the next N days.")
def forecast(
    location: Annotated[str, Field(description="City or place name")],
    days: Annotated[int, Field(ge=1, le=7, description="Number of days to get a forecast, defaults to 7 if not provided")] = 7,
) -> list[dict]:
    lat, lon = resolve_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_sum,precipitation_probability_max,precipitation_hours,wind_speed_10m_max",
        "timezone": "auto",
    }
    daily = (
        requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        .json()
        .get("daily", {})
    )
    return [
        {
            "date": daily["time"][i],
            "max_temp_c": daily["temperature_2m_max"][i],
            "min_temp_c": daily["temperature_2m_min"][i],
            "wind_max_kph": daily["wind_speed_10m_max"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "precipitation_probability": daily["precipitation_probability_max"][i],
            "uv_index": daily["uv_index_max"][i],
            "uv_risk_level": get_uv_risk(daily["uv_index_max"][i]),
            "condition": weather_codes.get(daily["weather_code"][i], "Unknown"),
        }
        for i in range(min(days, len(daily.get("time", []))))
    ]


@mcp.tool(description="Get UV index forecast and risk level for the next few days.")
def uv_index(location: Annotated[str, Field(description="City or place name")]) -> list[dict]:
    lat, lon = resolve_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "uv_index_max",
        "timezone": "auto",
    }
    daily = (
        requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        .json()
        .get("daily", {})
    )
    return [
        {
            "date": daily["time"][i],
            "uv_index": daily["uv_index_max"][i],
            "risk_level": get_uv_risk(daily["uv_index_max"][i])
        }
        for i in range(len(daily.get("time", [])))
    ]


@mcp.tool(description="Get air quality index values (PM10, PM2.5, ozone) for a location.")
def air_quality(location: Annotated[str, Field(description="City or place name")]) -> dict:
    lat, lon = resolve_location(location)
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "us_aqi,pm10,pm2_5,ozone",
        "timezone": "auto"
    }
    quality = requests.get(url, params=params).json().get("current", {})
    return {
        "us_aqi": quality.get("us_aqi", [None]),
        "pm10": quality.get("pm10", [None]),
        "pm2_5": quality.get("pm2_5", [None]),
        "ozone": quality.get("ozone", [None]),
        "time": quality.get("time", [None])
    }




def main() -> None:
    """Run the Weather MCP server."""
    start_mcp(mcp, "Start the Weather MCP server.")


if __name__ == "__main__":
    main()
