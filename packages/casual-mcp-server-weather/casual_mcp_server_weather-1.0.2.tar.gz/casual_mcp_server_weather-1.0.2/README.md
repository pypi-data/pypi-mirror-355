# Weather MCP Server

Weather forecast and air quality utilities using Open‑Meteo.

The server can be accessed locally over Stdio or remotely over Streamable HTTP.

## Tools

The tools exposed by the MCP server include:

- **current_weather** - Current temperature, wind speed and condition for a location.
- **forecast** - Daily forecast for the next few days.
- **uv_index** - UV index forecast and risk levels.
- **air_quality** - Air quality index values for a location.

---

## 🛠️ Installation

### Local Development (via `uv`)

From this directory:

```bash
uv sync --locked
uv tool install .
```

### Docker Build

From the root of the repository:

```bash
docker build -f servers/weather/Dockerfile -t casual-mcp-server-weather .
```

---

## ▶️ Running the Server

### ➤ Stdio Mode

#### From Source

Install for local development and then configure:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["tool", "run", "casual-mcp-server-weather"]
    }
  }
}
```

#### Using `uvx`

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["casual-mcp-server-weather"]
    }
  }
}
```

#### Docker

```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": ["run", "--rm", "casual-mcp-server-weather"]
    }
  }
}
```

---

### ➤ Streamable HTTP Mode

#### From Source

```bash
uv run casual-mcp-server-weather --transport streamable-http
```

With port/host overrides:

```bash
uv run casual-mcp-server-weather --transport streamable-http --port 9000 --host 0.0.0.0
```

#### Using `uvx`

```bash
uvx casual-mcp-server-weather --transport streamable-http
```

You can use the same port/host overrides as above

#### Docker

```bash
docker run -e MCP_TRANSPORT=streamable-http -e MCP_PORT=9000 -p 9000:9000 casual-mcp-server-weather
```

##### Configuration

```json
{
  "mcpServers": {
    "weather": {
      "type": "streamable-http",
      "url": "http://localhost:9000"
    }
  }
}
```

---

## 📜 License

MIT – [LICENSE](https://github.com/casualgenius/mcp-servers/blob/main/LICENSE)

---

## 📦 PyPI

Published at: [https://pypi.org/project/casual-mcp-server-weather/](https://pypi.org/project/casual-mcp-server-weather/)