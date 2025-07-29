"""Weather Union MCP Server.

A Model Context Protocol server that provides weather data from the Weather Union API.
This server offers tools to fetch current weather information for specific coordinates
or predefined cities in India.
"""

import argparse
import os
import sys
from typing import Optional
from dotenv import load_dotenv

import requests
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP(
    "Weather Union",
    instructions="A Model Context Protocol server for accessing Weather Union weather data and air quality information"
)

# Global variable to store the API key
API_KEY: Optional[str] = None

# Weather template defined at module level
WEATHER_TEMPLATE = """
Weather Information (Lat: {lat}, Lon: {lon}):

Temperature: {temp}°C
Humidity: {humidity}%
Wind Speed: {wind_speed} km/h
Wind Direction: {wind_dir}°
Rain Intensity: {rain_intensity} mm/h
Rain Accumulation: {rain_accum} mm
Air Quality Index (PM 2.5): {aqi_pm25}
Air Quality Index (PM 10): {aqi_pm10}
""".strip()


def get_weather_data(latitude: float, longitude: float) -> str:
    """Fetch and format weather data from the Weather Union API.
    
    Args:
        latitude: The latitude coordinate of the location (-90 to 90).
        longitude: The longitude coordinate of the location (-180 to 180).
        
    Returns:
        A formatted string containing weather information including temperature,
        humidity, wind data, precipitation, and air quality indices.
        
    Raises:
        ValueError: If the API key is not available.
        Exception: If the API request fails or returns invalid data.
    """
    if not API_KEY:
        raise ValueError("API key not provided. Please set the WEATHER_UNION_API_KEY environment variable.")
    
    url = "https://www.weatherunion.com/gw/weather/external/v0/get_weather_data"
    
    querystring = {
        "latitude": latitude,
        "longitude": longitude
    }
    
    headers = {
        "X-Zomato-Api-Key": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        
        # Format the response for better readability
        if 'locality_weather_data' in weather_data:
            locality_data = weather_data['locality_weather_data']

            formatted_weather = WEATHER_TEMPLATE.format(
                lat=latitude,
                lon=longitude,
                temp=locality_data.get('temperature', 'N/A'),
                humidity=locality_data.get('humidity', 'N/A'),
                wind_speed=locality_data.get('wind_speed', 'N/A'),
                wind_dir=locality_data.get('wind_direction', 'N/A'),
                rain_intensity=locality_data.get('rain_intensity', 'N/A'),
                rain_accum=locality_data.get('rain_accumulation', 'N/A'),
                aqi_pm25=locality_data.get('aqi_pm_2_point_5', 'N/A'),
                aqi_pm10=locality_data.get('aqi_pm_10', 'N/A')
            )
            
            return formatted_weather
        else:
            return f"Weather data retrieved: {weather_data}"
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch weather data: {str(e)}")


@mcp.tool(
    description="Get current weather data for a specific geographic location using latitude and longitude coordinates"
)
def get_current_weather(latitude: float, longitude: float) -> str:
    """Get current weather data for a specific location.
    
    This tool fetches real-time weather information including temperature, humidity,
    wind conditions, precipitation, and air quality data for any geographic location
    specified by latitude and longitude coordinates.
    
    Args:
        latitude: The latitude coordinate of the location (-90 to 90 degrees).
        longitude: The longitude coordinate of the location (-180 to 180 degrees).
        
    Returns:
        A formatted string containing comprehensive weather information including:
        - Temperature in Celsius
        - Humidity percentage
        - Wind speed and direction
        - Rain intensity and accumulation
        - Air Quality Index for PM 2.5 and PM 10
    """
    try:
        return get_weather_data(latitude, longitude)
    except Exception as e:
        return f"Error retrieving weather data: {str(e)}"


@mcp.tool(
    description="Get weather data for major Indian cities using predefined city names"
)
def get_weather_for_city(city_name: str, country_code: str = "IN") -> str:
    """Get weather data for a predefined city in India.
    
    This tool provides weather information for major Indian cities using predefined
    coordinates. It's a convenient way to get weather data without needing to look up
    specific latitude and longitude coordinates.
    
    Args:
        city_name: The name of the city (case-insensitive). Supported cities include:
                  Bangalore, Mumbai, Delhi, Hyderabad, Chennai, Kolkata, Pune,
                  Ahmedabad, Jaipur, and Lucknow.
        country_code: The country code (default: "IN" for India). Currently only
                     Indian cities are supported.
        
    Returns:
        A formatted string containing weather information for the specified city,
        or an error message if the city is not found in the predefined list.
    """
    # Predefined coordinates for major Indian cities
    city_coordinates = {
        "bangalore": (12.933756, 77.625825),
        "mumbai": (19.075984, 72.877656),
        "delhi": (28.704060, 77.102493),
        "hyderabad": (17.385044, 78.486671),
        "chennai": (13.082680, 80.270721),
        "kolkata": (22.572646, 88.363895),
        "pune": (18.520430, 73.856744),
        "ahmedabad": (23.022505, 72.571362),
        "jaipur": (26.906677, 75.806770),
        "lucknow": (26.846694, 80.946166)
    }
    
    city_lower = city_name.lower()
    if city_lower in city_coordinates:
        lat, lon = city_coordinates[city_lower]
        try:
            return get_weather_data(lat, lon)
        except Exception as e:
            return f"Error retrieving weather data for {city_name}: {str(e)}"
    else:
        available_cities = ", ".join(city_coordinates.keys())
        return f"City '{city_name}' not found in predefined list. Available cities: {available_cities}"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        An argparse.Namespace object containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Weather Union MCP Server - A Model Context Protocol server for weather data"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport instead of stdin (default: stdin)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the HTTP server on (default: 8000, only used with --http)"
    )
    
    return parser.parse_args()


def setup_api_key() -> None:
    """Set up the API key from environment variable.
    
    Reads the Weather Union API key from the WEATHER_UNION_API_KEY environment
    variable and validates it by making a test API call.
    
    Raises:
        SystemExit: If the API key is not found or validation fails.
    """
    load_dotenv()
    global API_KEY
    
    # Read API key from environment variable
    API_KEY = os.getenv("WEATHER_UNION_API_KEY")
    if not API_KEY:
        print("✗ Error: WEATHER_UNION_API_KEY environment variable not set")
        print("Please set your Weather Union API key:")
        print("export WEATHER_UNION_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Validate API key by making a test request
    try:
        print("Validating API key...")
        test_result = get_weather_data(12.933756, 77.625825)  # Test with Bangalore coordinates
        print("✓ API key validated successfully")
    except Exception as e:
        print(f"✗ API key validation failed: {e}")
        print("Please check your WEATHER_UNION_API_KEY environment variable")
        sys.exit(1)


def main() -> None:
    """Main entry point for the MCP server.
    
    Sets up the API key, parses command line arguments, and starts the appropriate
    transport (stdin by default, HTTP if --http flag is used).
    """
    # Setup API key from environment
    setup_api_key()
    
    # Parse command line arguments
    args = parse_args()
    
    # Display server information
    if args.http:
        print(f"Starting Weather Union MCP Server on HTTP port {args.port}...")
        transport = "streamable-http"
        transport_kwargs = {"port": args.port}
    else:
        print("Starting Weather Union MCP Server on stdin...")
        transport = "stdio"
        transport_kwargs = {}
    
    print("Available tools:")
    print("  - get_current_weather: Get weather data for specific coordinates")
    print("  - get_weather_for_city: Get weather data for predefined Indian cities")
    print("Environment:")
    print(f"  - API Key: {'✓ Set' if API_KEY else '✗ Not set'}")
    print(f"  - Transport: {transport}")
    
    # Run the FastMCP server
    mcp.run(transport=transport, **transport_kwargs)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1) 