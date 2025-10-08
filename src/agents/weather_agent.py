"""Weather-specialized agent for city weather information."""

import re
from typing import List, Optional

from langchain_core.tools import BaseTool as LangChainBaseTool

from src.core.base_agent import BaseAgent, AgentFactory
from src.tools.weather_tools import get_weather_data, search_city_info
from src.config.settings import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherAgent(BaseAgent):
    """Specialized agent for weather-related queries and city climate information."""
    
    def __init__(self, tools: Optional[List[LangChainBaseTool]] = None):
        # Default tools for weather agent
        if tools is None:
            tools = [get_weather_data, search_city_info]
        
        # Get agent config from settings
        agent_config = config.agents.get("weather_agent")
        
        super().__init__(
            name="Weather Agent",
            description="Specialized agent for weather-related queries and city climate information",
            tools=tools,
            agent_config=agent_config
        )
        
        # Weather-specific keywords for query classification
        self.weather_keywords = {
            'weather', 'temperature', 'climate', 'rain', 'snow', 'storm', 'sunny', 
            'cloudy', 'humidity', 'wind', 'forecast', 'hot', 'cold', 'warm', 'cool',
            'precipitation', 'atmospheric', 'meteorological', 'conditions'
        }
        
        self.city_keywords = {
            'capital', 'city', 'town', 'metropolis', 'urban', 'municipal', 'district'
        }
    
    def can_handle(self, query: str) -> bool:
        """Determine if this agent can handle the given query."""
        query_lower = query.lower()
        
        # Check for weather-related keywords
        has_weather_keywords = any(keyword in query_lower for keyword in self.weather_keywords)
        
        # Check for city-related keywords
        has_city_keywords = any(keyword in query_lower for keyword in self.city_keywords)
        
        # Check for patterns that suggest weather queries
        weather_patterns = [
            r'weather\s+in\s+\w+',
            r'temperature\s+in\s+\w+',
            r'climate\s+of\s+\w+',
            r'how\s+is\s+the\s+weather',
            r'what\s+is\s+the\s+weather',
            r'weather\s+condition',
            r'current\s+weather'
        ]
        
        has_weather_pattern = any(re.search(pattern, query_lower) for pattern in weather_patterns)
        
        # This agent can handle queries that:
        # 1. Have weather keywords
        # 2. Have city keywords combined with weather context
        # 3. Match specific weather query patterns
        # 4. Ask about capital cities (often followed by weather queries)
        
        can_handle = (
            has_weather_keywords or 
            (has_city_keywords and ('weather' in query_lower or 'temperature' in query_lower)) or
            has_weather_pattern or
            'capital' in query_lower  # Capital city queries often lead to weather
        )
        
        logger.debug(f"WeatherAgent.can_handle('{query}'): {can_handle}")
        return can_handle
    
    def get_specialized_prompt(self) -> Optional[str]:
        """Get weather agent-specific prompt modifications."""
        return """
You are a specialized Weather Agent focused on providing accurate, real-time weather information for cities around the world.

Your expertise includes:
- Current weather conditions (temperature, humidity, wind, pressure)
- Weather descriptions and atmospheric conditions
- Geographic information about cities and locations
- Climate patterns and seasonal information

When handling weather queries:
1. Always use the get_weather_data tool for current weather information
2. Use search_city_info tool for general city information when needed
3. For queries about capitals, first find the capital city, then get its weather
4. Provide comprehensive weather details including temperature, conditions, humidity, wind, and pressure
5. Format responses in a clear, user-friendly manner
6. If weather data is unavailable, explain the limitation and suggest alternatives

Format your responses to be informative yet concise, focusing on the most relevant weather information for the user's query.
"""
    
    def _extract_cities_from_query(self, query: str) -> List[str]:
        """Extract potential city names from the query."""
        # This is a simple extraction - in production, you might use NLP libraries
        cities = []
        
        # Look for patterns like "weather in [City]", "temperature in [City]"
        patterns = [
            r'weather\s+in\s+([A-Za-z\s]+?)(?:\s|$|,|\?|!)',
            r'temperature\s+in\s+([A-Za-z\s]+?)(?:\s|$|,|\?|!)',
            r'climate\s+of\s+([A-Za-z\s]+?)(?:\s|$|,|\?|!)',
            r'capital\s+of\s+([A-Za-z\s]+?)(?:\s|$|,|\?|!)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            cities.extend([match.strip() for match in matches if match.strip()])
        
        return cities
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess the query to optimize for weather tasks."""
        # Extract cities mentioned in the query
        cities = self._extract_cities_from_query(query)
        
        if cities:
            logger.info(f"Detected cities in query: {cities}")
        
        # Add context hints for better agent performance
        if 'capital' in query.lower() and 'weather' not in query.lower():
            query += " and then find its current weather condition"
        
        return query


# Register the weather agent with the factory
AgentFactory.register_agent("weather", WeatherAgent)

# Export for easy importing
__all__ = ["WeatherAgent"]