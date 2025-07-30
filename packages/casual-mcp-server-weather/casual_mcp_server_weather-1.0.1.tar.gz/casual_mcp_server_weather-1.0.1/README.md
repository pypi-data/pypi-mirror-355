# Weather MCP Server

Weather forecast and air quality utilities using Open‑Meteo served via FastMCP.

The server can be accessed locally over Stdio or remotely over SSE/Streamable HTTP.

## Tools

The tools exposed by the MCP server include:

- **current_weather** - Current temperature, wind speed and condition for a location.
- **forecast** - Daily forecast for the next few days.
- **uv_index** - UV index forecast and risk levels.
- **air_quality** - Air quality index values for a location.

## Run with Python

```bash
cd servers/weather
uv pip install --system .
python -m casual_mcp_server_weather.server
```

## Run with `uvx`

```bash
uvx casual-mcp-server-weather
```

## Run with Docker

```bash
docker build -t casual-mcp-server-weather .
docker run -p 8000:8000 casual-mcp-server-weather
```
