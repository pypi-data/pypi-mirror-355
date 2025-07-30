from typing import Dict, List

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server with service name
mcp = FastMCP("WeatherService")


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get current weather description for a location."""
    return f"It's always sunny in {location}"


@mcp.tool()
async def get_temperature(location: str) -> Dict[str, float]:
    """Get current temperature for a location in Celsius and Fahrenheit."""
    # Simulated temperature data
    celsius = 25.0
    fahrenheit = celsius * 9 / 5 + 32
    return {"celsius": celsius, "fahrenheit": fahrenheit, "location": location}


@mcp.tool()
async def get_forecast(location: str, days: int = 3) -> List[Dict[str, str]]:
    """Get weather forecast for the next specified number of days."""
    if days < 1 or days > 7:
        raise ValueError("Days must be between 1 and 7")

    forecast = []
    for i in range(days):
        forecast.append({
            "day": f"Day {i + 1}",
            "location": location,
            "condition": "Sunny",
            "high_celsius": 25.0 + i,
            "low_celsius": 15.0 + i
        })
    return forecast


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
