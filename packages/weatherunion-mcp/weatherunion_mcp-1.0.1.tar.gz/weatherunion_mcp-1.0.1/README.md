# Weather Union MCP Server

A Model Context Protocol (MCP) server that provides weather data and air quality information using the [Weather Union API](https://www.weatherunion.com/). 

This server offers real-time weather data for specific coordinates or predefined Indian cities.

## Usage with MCP Clients

### Claude Desktop
Add to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "weather-union": {
      "command": "uvx",
      "args": ["weatherunion-mcp"],
      "env": {
        "WEATHER_UNION_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Other MCP Clients
The server follows standard MCP protocol and works with any compliant MCP client.

## Quick Start

1. **Set up your API key:**
   ```bash
   export WEATHER_UNION_API_KEY='your-api-key-here'
   ```

2. **Run the server:**
   ```bash
   # For MCP clients (default - uses stdin)
   python weatherunion_mcp/server.py
   
   # For testing with HTTP
   python weatherunion_mcp/server.py --http --port 8000
   ```

## Available Tools

The MCP server provides two powerful weather tools:

### 1. `get_current_weather`
Get current weather data for any geographic location using latitude and longitude coordinates.

**Parameters:**
- `latitude` (float): Latitude coordinate (-90 to 90 degrees)
- `longitude` (float): Longitude coordinate (-180 to 180 degrees)

**Returns:**
Comprehensive weather information including temperature, humidity, wind conditions, precipitation, and air quality data.

**Example:**
```
get_current_weather(12.933756, 77.625825)  # Bangalore coordinates
```

### 2. `get_weather_for_city`
Get weather data for major Indian cities using predefined city names.

**Parameters:**
- `city_name` (str): Name of the city (case-insensitive)
- `country_code` (str, optional): Country code (default: "IN")

**Supported Cities:**
- Bangalore, Mumbai, Delhi, Hyderabad, Chennai
- Kolkata, Pune, Ahmedabad, Jaipur, Lucknow

**Example:**
```
get_weather_for_city("bangalore")
get_weather_for_city("Mumbai")
```

## Weather Data Format

The server returns comprehensive weather information in a formatted string:

```
Weather Information (Lat: 12.933756, Lon: 77.625825):

Temperature: 25.68°C
Humidity: 25.81%
Wind Speed: 1.15 km/h
Wind Direction: 331.2°
Rain Intensity: 0 mm/h
Rain Accumulation: 0.4 mm
Air Quality Index (PM 2.5): 84
Air Quality Index (PM 10): 75
```

## API Key

You need a Weather Union API key (X-Zomato-Api-Key) to use this server. You can generate this for free by signing up at [Weather Union](https://www.weatherunion.com/).

- The server validates your API key on startup
- API key must be set as an environment variable
- The server will show clear error messages if the API key is missing or invalid

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is open source. See the LICENSE file for details.