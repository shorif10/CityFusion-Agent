"""
CityFusion-Agent: Real-time city insights through intelligent agents.
"""

__version__ = "0.1.0"
__author__ = "CityFusion Team"
__description__ = "Modular agent framework for real-time city insights"

from src.core.orchestrator import AgentOrchestrator
from src.agents.weather_agent import WeatherAgent

__all__ = ["AgentOrchestrator", "WeatherAgent"]