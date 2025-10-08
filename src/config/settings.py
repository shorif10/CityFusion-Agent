"""Configuration settings for CityFusion-Agent."""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """LLM configuration settings."""
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    
    def __post_init__(self):
        """Set API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")


@dataclass
class WeatherConfig:
    """Weather service configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))
    base_url: str = "https://api.weatherstack.com/current"
    timeout: int = 30
    
    def __post_init__(self):
        """Validate required configurations."""
        if not self.api_key:
            raise ValueError("Weather API key is required. Set WEATHER_API_KEY environment variable.")


@dataclass
class AgentConfig:
    """Agent-specific configuration."""
    name: str
    description: str
    tools: list = field(default_factory=list)
    max_iterations: int = 10
    verbose: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create AgentConfig from dictionary."""
        return cls(**data)


@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str = "CityFusion-Agent"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    llm: LLMConfig = field(default_factory=LLMConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        """Load configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create AppConfig from dictionary."""
        # Extract nested configs
        llm_data = data.pop('llm', {})
        weather_data = data.pop('weather', {})
        agents_data = data.pop('agents', {})
        
        # Create nested config objects
        llm_config = LLMConfig(**llm_data)
        weather_config = WeatherConfig(**weather_data)
        agents_config = {
            name: AgentConfig.from_dict(config) 
            for name, config in agents_data.items()
        }
        
        return cls(
            llm=llm_config,
            weather=weather_config,
            agents=agents_config,
            **data
        )
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to file."""
        config_dict = {
            'app_name': self.app_name,
            'version': self.version,
            'debug': self.debug,
            'log_level': self.log_level,
            'llm': {
                'model_name': self.llm.model_name,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
            },
            'weather': {
                'base_url': self.weather.base_url,
                'timeout': self.weather.timeout,
            },
            'agents': {
                name: {
                    'name': agent.name,
                    'description': agent.description,
                    'tools': agent.tools,
                    'max_iterations': agent.max_iterations,
                    'verbose': agent.verbose,
                }
                for name, agent in self.agents.items()
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)


# Global configuration instance
config = AppConfig.load_from_file()