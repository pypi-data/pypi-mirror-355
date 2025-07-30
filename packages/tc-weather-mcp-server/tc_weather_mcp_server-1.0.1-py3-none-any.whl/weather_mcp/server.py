"""Weather MCP Server with NWS API integration"""

from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(name="WeatherMCP", version="1.0.0")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "tc-weather-mcp-server/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NWS API request failed: {e}")
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers (demo tool)"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY, TX)
    """
    if len(state) != 2:
        return "Please provide a valid 2-letter US state code (e.g., CA, NY, TX)"
    
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return f"No active weather alerts for {state.upper()}."

    alerts = [format_alert(feature) for feature in data["features"]]
    return f"Active weather alerts for {state.upper()}:\n" + "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return "Invalid latitude. Must be between -90 and 90."
    if not (-180 <= longitude <= 180):
        return "Invalid longitude. Must be between -180 and 180."
    
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location. This may be outside the US."

    try:
        # Get the forecast URL from the points response
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)

        if not forecast_data:
            return "Unable to fetch detailed forecast."

        # Format the periods into a readable forecast
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:  # Only show next 5 periods
            forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
            forecasts.append(forecast)

        location_name = points_data["properties"]["relativeLocation"]["properties"]["city"] + ", " + points_data["properties"]["relativeLocation"]["properties"]["state"]
        return f"Weather forecast for {location_name}:\n" + "\n---\n".join(forecasts)
    
    except KeyError as e:
        return f"Error parsing forecast data: {e}"
