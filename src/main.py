import sys
import argparse
import json
from typing import Optional
from pathlib import Path

from src.core.orchestrator import AgentOrchestrator
from src.config.settings import config
from src.utils.logger import get_logger, setup_logging
from src.utils.monitoring import app_monitor
from src.utils.exceptions import CityFusionError, ConfigurationError

logger = get_logger(__name__)


class CityFusionApp:
    """Main CityFusion-Agent application."""
    
    def __init__(self):
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.is_initialized = False
    
    def initialize(self) -> None:
        """Initialize the application."""
        try:
            logger.info("Initializing CityFusion-Agent...")
            
            # Validate configuration
            self._validate_configuration()
            
            # Initialize orchestrator
            self.orchestrator = AgentOrchestrator()
            
            # Start monitoring
            app_monitor.start_monitoring()
            
            self.is_initialized = True
            logger.info("CityFusion-Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise CityFusionError(f"Application initialization failed: {str(e)}") from e
    
    def _validate_configuration(self) -> None:
        """Validate critical configuration settings."""
        if not config.llm.api_key:
            raise ConfigurationError(
                "Google API key is required. Please set GOOGLE_API_KEY environment variable."
            )
        
        if not config.weather.api_key:
            raise ConfigurationError(
                "Weather API key is required. Please set WEATHER_API_KEY environment variable."
            )
        
        logger.info("Configuration validation passed")
    
    def run_query(self, query: str, verbose: bool = False) -> dict:
        """Run a single query through the orchestrator."""
        if not self.is_initialized:
            raise CityFusionError("Application not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Processing query: {query}")
            response = self.orchestrator.execute_query(query)
            
            # Record metrics
            app_monitor.record_agent_query(
                response.agent_name, 
                response.success, 
                response.execution_time
            )
            
            result = {
                "success": response.success,
                "output": response.output,
                "agent_name": response.agent_name,
                "execution_time": response.execution_time,
                "error": response.error
            }
            
            if verbose:
                result["intermediate_steps"] = response.intermediate_steps
                result["metadata"] = response.metadata
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            app_monitor.record_error("query_execution_error")
            return {
                "success": False,
                "output": "",
                "agent_name": "unknown",
                "execution_time": 0.0,
                "error": str(e)
            }
    
    def run_interactive(self) -> None:
        """Run in interactive mode."""
        if not self.is_initialized:
            self.initialize()
        
        print("\\n🌟 Welcome to CityFusion-Agent! 🌟")
        print("Your intelligent city insights companion.")
        print("Type 'help' for commands, 'quit' to exit.\\n")
        
        while True:
            try:
                query = input("CityFusion> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Thank you for using CityFusion-Agent! Goodbye! 👋")
                    break
                
                if query.lower() == 'help':
                    self._show_help()
                    continue
                
                if query.lower() == 'status':
                    self._show_status()
                    continue
                
                if query.lower() == 'agents':
                    self._show_agents()
                    continue
                
                if not query:
                    continue
                
                # Execute the query
                result = self.run_query(query)
                
                if result["success"]:
                    print(f"\\n✅ {result['output']}")
                    print(f"   ⏱️  Processed by {result['agent_name']} in {result['execution_time']:.2f}s")
                else:
                    print(f"\\n❌ Error: {result['error']}")
                
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\\n\\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\\n❌ Unexpected error: {str(e)}")
                logger.error(f"Interactive mode error: {str(e)}")
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
🔧 Available Commands:
  help     - Show this help message
  status   - Show application status and health
  agents   - List available agents and their capabilities
  quit     - Exit the application
  
💡 Example Queries:
  • "Find the capital of Bangladesh, then find its current weather condition"
  • "What's the weather like in Dhaka?"
  • "Show me weather conditions in Rajshahi"
  • "What's the temperature in London?"
  
🌟 Tips:
  • Ask about weather conditions in any city
  • Query for capital cities and their weather
  • Use natural language - I'll understand!
        """
        print(help_text)
    
    def _show_status(self) -> None:
        """Show application status."""
        try:
            health = app_monitor.get_health_status()
            summary = app_monitor.get_application_summary()
            
            print("\\n📊 Application Status:")
            print(f"   Status: {health['status'].upper()}")
            print(f"   Uptime: {summary.get('uptime_human', 'Unknown')}")
            print(f"   Total Queries: {health.get('total_queries', 0)}")
            
            if health.get('warnings'):
                print("\\n⚠️  Warnings:")
                for warning in health['warnings']:
                    print(f"   • {warning}")
            
            # Agent statistics
            if summary.get('agents'):
                print("\\n🤖 Agent Statistics:")
                for agent_name, stats in summary['agents'].items():
                    print(f"   {agent_name}: {stats['total_queries']} queries, "
                          f"{stats['success_rate']:.1f}% success rate")
        
        except Exception as e:
            print(f"❌ Could not retrieve status: {str(e)}")
    
    def _show_agents(self) -> None:
        """Show available agents."""
        try:
            capabilities = self.orchestrator.get_agent_capabilities()
            
            print("\\n🤖 Available Agents:")
            for agent in capabilities.get('agents', []):
                print(f"   • {agent['name']}: {agent['description']}")
                print(f"     Tools: {', '.join(agent['tools'])}")
                print(f"     Model: {agent['model']}")
                print()
        
        except Exception as e:
            print(f"❌ Could not retrieve agent information: {str(e)}")
    
    def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Shutting down CityFusion-Agent...")
        
        # Stop monitoring
        app_monitor.stop_monitoring()
        
        logger.info("CityFusion-Agent shutdown complete")


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="CityFusion-Agent: Real-time city insights through intelligent agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cityfusion                              # Interactive mode
  python -m cityfusion --query "Weather in Dhaka"  # Single query
  python -m cityfusion --status                     # Show status
  python -m cityfusion --health                     # Health check
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Execute a single query and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show application status and exit"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Show health check and exit"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level"
    )
    
    return parser


def main() -> None:
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Setup logging
    if args.log_level:
        setup_logging(log_level=args.log_level)
    
    # Create application instance
    app = CityFusionApp()
    
    try:
        # Handle different modes
        if args.health:
            app.initialize()
            health = app.orchestrator.health_check()
            print(json.dumps(health, indent=2))
            return
        
        if args.status:
            app.initialize()
            summary = app_monitor.get_application_summary()
            print(json.dumps(summary, indent=2, default=str))
            return
        
        if args.query:
            app.initialize()
            result = app.run_query(args.query, verbose=args.verbose)
            
            if result["success"]:
                print(result["output"])
                if args.verbose:
                    print(f"\\nAgent: {result['agent_name']}")
                    print(f"Execution Time: {result['execution_time']:.2f}s")
            else:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
        else:
            # Interactive mode
            app.run_interactive()
    
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user")
    except CityFusionError as e:
        logger.error(f"CityFusion error: {e.message}")
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()