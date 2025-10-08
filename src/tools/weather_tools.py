"""Weather-related tools for city weather information."""

import requests
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from src.tools.base_tool import BaseTool, ToolResult
from src.config.settings import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherAPITool(BaseTool):
    """Tool for fetching weather data from weather API."""
    
    def __init__(self):
        super().__init__(
            name="weather_api",
            description="Fetch current weather data for a given city using weather API"
        )
        self.api_key = config.weather.api_key
        self.base_url = config.weather.base_url
        self.timeout = config.weather.timeout
    
    def validate_input(self, city: str = None, **kwargs) -> bool:
        """Validate input parameters."""
        if not city or not isinstance(city, str):
            return False
        if not self.api_key:
            logger.error("Weather API key not configured")
            return False
        return True
    
    def execute(self, city: str, **kwargs) -> ToolResult:
        """Execute weather API call."""
        if not self.validate_input(city=city):
            return ToolResult(
                success=False,
                error="Invalid input parameters or missing API key"
            )
        
        try:
            url = f"{self.base_url}?access_key={self.api_key}&query={city}"
            logger.info(f"Fetching weather data for city: {city}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if API returned an error
            if 'error' in data:
                error_msg = data['error'].get('info', 'Unknown API error')
                logger.error(f"Weather API error: {error_msg}")
                return ToolResult(
                    success=False,
                    error=f"Weather API error: {error_msg}"
                )
            
            # Format the weather data
            if 'current' in data and 'location' in data:
                formatted_data = self._format_weather_data(data)
                return ToolResult(
                    success=True,
                    data=formatted_data,
                    metadata={"source": "weatherstack", "city": city}
                )
            else:
                return ToolResult(
                    success=False,
                    error="Invalid response format from weather API"
                )
                
        except requests.exceptions.Timeout:
            logger.error(f"Weather API timeout for city: {city}")
            return ToolResult(
                success=False,
                error="Weather API request timed out"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Weather API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in weather API call: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _format_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw weather API data into a more readable format."""
        current = data.get('current', {})
        location = data.get('location', {})
        
        return {
            "location": {
                "name": location.get('name'),
                "region": location.get('region'),
                "country": location.get('country'),
                "coordinates": {
                    "latitude": location.get('lat'),
                    "longitude": location.get('lon')
                }
            },
            "current_weather": {
                "temperature": current.get('temperature'),
                "feels_like": current.get('feelslike'),
                "weather_description": current.get('weather_descriptions', [None])[0],
                "humidity": current.get('humidity'),
                "wind_speed": current.get('wind_speed'),
                "wind_direction": current.get('wind_dir'),
                "pressure": current.get('pressure'),
                "visibility": current.get('visibility'),
                "uv_index": current.get('uv_index'),
                "observation_time": current.get('observation_time')
            }
        }


class CitySearchTool(BaseTool):
    """Tool for searching city information using DuckDuckGo."""
    
    def __init__(self):
        super().__init__(
            name="city_search",
            description="Search for general information about cities using DuckDuckGo"
        )
        self.search_tool = DuckDuckGoSearchRun()
    
    def validate_input(self, query: str = None, **kwargs) -> bool:
        """Validate input parameters."""
        return query and isinstance(query, str) and len(query.strip()) > 0
    
    def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute city search."""
        if not self.validate_input(query=query):
            return ToolResult(
                success=False,
                error="Invalid query parameter"
            )
        
        try:
            logger.info(f"Searching for city information: {query}")
            result = self.search_tool.run(query)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"source": "duckduckgo", "query": query}
            )
            
        except Exception as e:
            logger.error(f"City search failed: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )


# LangChain tool wrappers for backward compatibility
weather_api_tool = WeatherAPITool()
city_search_tool = CitySearchTool()


@tool
def get_weather_data(city: str) -> str:
    """Fetch current weather data for a given city."""
    result = weather_api_tool.execute(city=city)
    
    if result.success:
        return str(result.data)
    else:
        return f"Error: {result.error}"


@tool
def search_city_info(query: str) -> str:
    """Search for general information about cities."""
    result = city_search_tool.execute(query=query)
    
    if result.success:
        return str(result.data)
    else:
        return f"Error: {result.error}"


# Export tools for easy importing
__all__ = [
    "WeatherAPITool",
    "CitySearchTool", 
    "get_weather_data",
    "search_city_info",
    "weather_api_tool",
    "city_search_tool"
]