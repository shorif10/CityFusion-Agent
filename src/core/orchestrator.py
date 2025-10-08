"""Agent orchestrator for managing multiple agents and routing queries."""

from typing import List, Dict, Any, Optional, Tuple
import time

from src.core.base_agent import BaseAgent, AgentResponse
from src.agents.weather_agent import WeatherAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple agents and routes queries to the most appropriate agent."""
    
    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.query_history: List[Dict[str, Any]] = []
        
        # Initialize default agents
        self._initialize_default_agents()
        
        logger.info(f"AgentOrchestrator initialized with {len(self.agents)} agents")
    
    def _initialize_default_agents(self) -> None:
        """Initialize default agents."""
        # Initialize weather agent
        weather_agent = WeatherAgent()
        self.register_agent(weather_agent)
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent with the orchestrator."""
        if agent.name not in self.agent_registry:
            self.agents.append(agent)
            self.agent_registry[agent.name] = agent
            logger.info(f"Registered agent: {agent.name}")
        else:
            logger.warning(f"Agent {agent.name} is already registered")
    
    def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent from the orchestrator."""
        if agent_name in self.agent_registry:
            agent = self.agent_registry.pop(agent_name)
            self.agents.remove(agent)
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        else:
            logger.warning(f"Agent {agent_name} not found for unregistration")
            return False
    
    def find_best_agent(self, query: str) -> Optional[BaseAgent]:
        """Find the best agent to handle the given query."""
        candidates = []
        
        for agent in self.agents:
            if agent.can_handle(query):
                candidates.append(agent)
                logger.debug(f"Agent {agent.name} can handle query: {query}")
        
        if not candidates:
            logger.warning(f"No agent found to handle query: {query}")
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # If multiple agents can handle the query, prioritize based on agent type
        # For now, we'll use a simple priority system
        priority_order = ["Weather Agent", "General Agent"]  # Add more as needed
        
        for priority_agent in priority_order:
            for candidate in candidates:
                if candidate.name == priority_agent:
                    logger.debug(f"Selected agent {candidate.name} based on priority")
                    return candidate
        
        # If no priority match, return the first candidate
        return candidates[0]
    
    def execute_query(self, query: str, **kwargs) -> AgentResponse:
        """Execute a query using the most appropriate agent."""
        start_time = time.time()
        
        # Find the best agent for the query
        selected_agent = self.find_best_agent(query)
        
        if selected_agent is None:
            # No suitable agent found
            logger.error(f"No suitable agent found for query: {query}")
            return AgentResponse(
                success=False,
                output="I'm sorry, but I couldn't find an appropriate agent to handle your query. Please try rephrasing your question or contact support.",
                intermediate_steps=[],
                execution_time=time.time() - start_time,
                agent_name="Orchestrator",
                error="No suitable agent found",
                metadata={"query": query, "available_agents": [a.name for a in self.agents]}
            )
        
        logger.info(f"Routing query to agent: {selected_agent.name}")
        
        # Preprocess query if the agent supports it
        processed_query = query
        if hasattr(selected_agent, 'preprocess_query'):
            processed_query = selected_agent.preprocess_query(query)
            if processed_query != query:
                logger.debug(f"Query preprocessed: '{query}' -> '{processed_query}'")
        
        # Execute the query with the selected agent
        response = selected_agent.execute(processed_query, **kwargs)
        
        # Log the query and response for analytics
        self._log_query_execution(query, selected_agent.name, response)
        
        return response
    
    def _log_query_execution(self, query: str, agent_name: str, response: AgentResponse) -> None:
        """Log query execution for analytics and debugging."""
        log_entry = {
            "timestamp": time.time(),
            "query": query,
            "agent_name": agent_name,
            "success": response.success,
            "execution_time": response.execution_time,
            "error": response.error
        }
        
        self.query_history.append(log_entry)
        
        # Keep only last 100 queries to prevent memory bloat
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all registered agents."""
        return {
            "total_agents": len(self.agents),
            "agents": [agent.get_capabilities() for agent in self.agents]
        }
    
    def get_agent_by_name(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a specific agent by name."""
        return self.agent_registry.get(agent_name)
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query execution statistics."""
        if not self.query_history:
            return {"message": "No queries executed yet"}
        
        total_queries = len(self.query_history)
        successful_queries = sum(1 for entry in self.query_history if entry["success"])
        failed_queries = total_queries - successful_queries
        
        avg_execution_time = sum(entry["execution_time"] for entry in self.query_history) / total_queries
        
        agent_usage = {}
        for entry in self.query_history:
            agent_name = entry["agent_name"]
            agent_usage[agent_name] = agent_usage.get(agent_name, 0) + 1
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (successful_queries / total_queries) * 100,
            "average_execution_time": avg_execution_time,
            "agent_usage": agent_usage
        }
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self.agent_registry.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all agents."""
        health_status = {
            "orchestrator_status": "healthy",
            "total_agents": len(self.agents),
            "agents": {}
        }
        
        for agent in self.agents:
            try:
                # Simple health check - check if agent can be initialized
                capabilities = agent.get_capabilities()
                health_status["agents"][agent.name] = {
                    "status": "healthy",
                    "tools_count": len(capabilities.get("tools", [])),
                    "model": capabilities.get("model", "unknown")
                }
            except Exception as e:
                health_status["agents"][agent.name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                logger.error(f"Health check failed for agent {agent.name}: {str(e)}")
        
        return health_status


# Export for easy importing
__all__ = ["AgentOrchestrator"]