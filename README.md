# CityFusion-Agent

<div align="center">

![CityFusion-Agent Logo](https://via.placeholder.com/200x100/1e3a8a/ffffff?text=CityFusion-Agent)

**Real-time city insights through intelligent agents**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## 🌟 Overview

CityFusion-Agent is a modular, scalable, and industry-standard AI agent framework designed to provide real-time insights about cities around the world. Built with LangChain and Google's Gemini AI, it currently specializes in weather information but is architected to easily support additional city-related services.

## ✨ Features

- **🤖 Intelligent Agent System**: Modular agent architecture with specialized agents for different domains
- **🌤️ Weather Intelligence**: Real-time weather data with comprehensive city information
- **🔧 Extensible Framework**: Easy to add new agents and tools for different city insights
- **📊 Built-in Monitoring**: System health monitoring and performance metrics
- **⚙️ Configuration Management**: Environment-based configuration with YAML support
- **🛡️ Error Handling**: Comprehensive error handling and logging
- **🎯 Smart Query Routing**: Automatic agent selection based on query content

## 🏗️ Architecture

```
cityfusion/
├── agents/           # Specialized agents (Weather, Traffic, etc.)
├── tools/            # Agent tools and utilities
├── core/             # Base framework and orchestrator
├── config/           # Configuration management
├── utils/            # Logging, monitoring, exceptions
└── main.py           # Application entry point
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- WeatherStack API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shorif10/CityFusion-Agent.git
   cd CityFusion-Agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env and add your API keys:
   # GOOGLE_API_KEY=your_google_gemini_api_key
   # WEATHER_API_KEY=your_weatherstack_api_key
   ```

### Usage

#### Interactive Mode
```bash
python -m src
```

#### Single Query
```bash
python -m src --query "What's the weather like in Dhaka?"
```

#### Using the convenience script
```bash
python run.py --query "Find the capital of Bangladesh and its weather"
```

## 💡 Example Queries

- "Find the capital of Bangladesh, then find its current weather condition"
- "What's the weather like in Dhaka?"
- "Show me weather conditions in Rajshahi"
- "What's the temperature in London right now?"

## 🔧 Configuration

The application supports flexible configuration through:

- **Environment variables** (`.env` file)
- **YAML configuration** (`cityfusion/config/config.yaml`)
- **Command-line arguments**

### Key Configuration Options

```yaml
# src/config/config.yaml
llm:
  model_name: "gemini-2.5-flash-lite"
  temperature: 0.7

weather:
  timeout: 30

agents:
  weather_agent:
    name: "Weather Agent"
    max_iterations: 10
    verbose: true
```

## 🏗️ Adding New Agents

The framework is designed for easy extension. Here's how to add a new agent:

1. **Create your agent class**
   ```python
   from src.core.base_agent import BaseAgent, AgentFactory
   
   class TrafficAgent(BaseAgent):
       def can_handle(self, query: str) -> bool:
           return "traffic" in query.lower()
       
       def get_specialized_prompt(self) -> str:
           return "You are a traffic information specialist..."
   
   # Register the agent
   AgentFactory.register_agent("traffic", TrafficAgent)
   ```

2. **Create specialized tools**
   ```python
   from src.tools.base_tool import BaseTool, ToolResult
   
   class TrafficTool(BaseTool):
       def execute(self, **kwargs) -> ToolResult:
           # Your tool logic here
           pass
   ```

3. **Update configuration**
   ```yaml
   agents:
     traffic_agent:
       name: "Traffic Agent"
       description: "Real-time traffic information"
       tools: ["traffic_info", "route_planning"]
   ```

## 📊 Monitoring and Health

The application includes comprehensive monitoring:

```bash
# Check application status
python -m src --status

# Health check
python -m src --health
```

### Monitoring Features

- **System Resources**: CPU, memory, disk usage
- **Agent Performance**: Query success rates, response times
- **Error Tracking**: Categorized error counting
- **API Usage**: External API call monitoring

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest -m unit
pytest -m integration
```

## 📋 Development

### Code Style

The project uses Black for code formatting:

```bash
# Format code
black src/

# Check formatting
black --check src/
```

### Type Checking

```bash
# Run type checking
mypy src/
```

### Development Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## 🛠️ API Keys Setup

### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file: `GOOGLE_API_KEY=your_key_here`

### WeatherStack API Key
1. Sign up at [WeatherStack](https://weatherstack.com/)
2. Get your free API key
3. Add to your `.env` file: `WEATHER_API_KEY=your_key_here`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Roadmap

- [ ] **Traffic Agent**: Real-time traffic information and route optimization
- [ ] **Events Agent**: City events, festivals, and activities
- [ ] **Tourism Agent**: Tourist attractions and recommendations
- [ ] **REST API**: HTTP API for external integrations
- [ ] **Web Interface**: Browser-based user interface
- [ ] **Mobile App**: Native mobile applications

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/shorif10/CityFusion-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/shorif10/CityFusion-Agent/discussions)
- **Email**: team@cityfusion.dev

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the agent framework
- [Google Gemini](https://ai.google.dev/) for the language model
- [WeatherStack](https://weatherstack.com/) for weather data
- [DuckDuckGo](https://duckduckgo.com/) for search capabilities

---

<div align="center">

**Made with ❤️ by the CityFusion Team**

[⭐ Star us on GitHub](https://github.com/shorif10/CityFusion-Agent) | [🐛 Report Bug](https://github.com/shorif10/CityFusion-Agent/issues) | [💡 Request Feature](https://github.com/shorif10/CityFusion-Agent/issues)

</div>
Merges AI reasoning with real-world city data
