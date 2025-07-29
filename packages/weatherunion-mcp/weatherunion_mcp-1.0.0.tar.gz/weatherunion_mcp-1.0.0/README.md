# Weather Union MCP Server

A Model Context Protocol (MCP) server that provides weather data using the Weather Union API.

## Quick Start

Run the server directly with uvx (recommended):

```bash
uvx weatherunion-mcp --api-key YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Weather Union API key (X-Zomato-Api-Key).

## Installation

### Option 1: Direct execution with uvx (Recommended)
```bash
uvx weatherunion-mcp --api-key YOUR_API_KEY
```

### Option 2: Install and run
```bash
pip install -e .
weatherunion-mcp --api-key YOUR_API_KEY
```

## Available Tools

The MCP server provides the following tools:

### 1. `get_current_weather`
Get formatted weather data for specific coordinates.

**Parameters:**
- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate

**Example:**
```
get_current_weather(12.933756, 77.625825)  # Bangalore coordinates
```

### 2. `get_weather_raw`
Get raw weather data as returned by the Weather Union API.

**Parameters:**
- `latitude` (float): Latitude coordinate  
- `longitude` (float): Longitude coordinate

### 3. `get_weather_for_city`
Get weather data for predefined major Indian cities.

**Parameters:**
- `city_name` (str): Name of the city
- `country_code` (str, optional): Country code (default: "IN")

**Supported Cities:**
- Bangalore, Mumbai, Delhi, Hyderabad, Chennai
- Kolkata, Pune, Ahmedabad, Jaipur, Lucknow

**Example:**
```
get_weather_for_city("bangalore")
```

## API Key

You need a Weather Union API key to use this server. This is the same as the X-Zomato-Api-Key.

The server will validate your API key on startup by making a test request.

## Usage with MCP Clients

Once the server is running, MCP clients (like Claude Desktop, Cline, etc.) can connect to it and use the weather tools.

Example weather data format:
```
Weather Information for HSR Layout:

Temperature: 25.2°C
Humidity: 68%
Wind Speed: 12.5 km/h
Wind Direction: 230°
Rain Intensity: 0.0 mm/h
Rain Accumulation: 0.0 mm

Last Updated: 2024-01-15T14:30:00Z
```

## Development

The server is built using [FastMCP](https://github.com/jlowin/fastmcp), which provides a simple way to create MCP servers in Python.

### Project Structure
```
weatherunion-mcp/
├── weatherunion_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
├── pyproject.toml         # Project configuration
└── README.md
```

### Testing
You can test the server by running it and checking the validation:
```bash
uvx weatherunion-mcp --api-key YOUR_API_KEY
```

The server will validate your API key on startup and show available tools.

## Requirements

- Python 3.13+
- fastmcp >= 0.2.0
- requests >= 2.31.0

## License

This project is open source. See the LICENSE file for details.

```json

```