"""Base agent framework for CityFusion-Agent."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain import hub

from src.config.settings import config, AgentConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Standardized agent response format."""
    success: bool
    output: str
    intermediate_steps: List[Dict[str, Any]]
    execution_time: float
    agent_name: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Abstract base class for all CityFusion agents."""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        tools: List[LangChainBaseTool],
        agent_config: Optional[AgentConfig] = None
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.config = agent_config or AgentConfig(name=name, description=description)
        self.llm = self._initialize_llm()
        self.agent_executor = self._initialize_agent()
        
        logger.info(f"Initialized agent: {self.name}")
    
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the LLM for this agent."""
        return ChatGoogleGenerativeAI(
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            google_api_key=config.llm.api_key
        )
    
    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the agent executor."""
        # Get ReAct prompt from hub
        prompt = hub.pull("hwchase17/react")
        
        # Create the agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True
        )
    
    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Determine if this agent can handle the given query."""
        pass
    
    @abstractmethod
    def get_specialized_prompt(self) -> Optional[str]:
        """Get agent-specific prompt modifications."""
        pass
    
    def execute(self, query: str, **kwargs) -> AgentResponse:
        """Execute the agent with the given query."""
        start_time = time.time()
        
        try:
            logger.info(f"Agent {self.name} executing query: {query}")
            
            # Prepare input
            agent_input = {"input": query}
            agent_input.update(kwargs)
            
            # Execute the agent
            result = self.agent_executor.invoke(agent_input)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                output=result.get("output", ""),
                intermediate_steps=result.get("intermediate_steps", []),
                execution_time=execution_time,
                agent_name=self.name,
                metadata={
                    "query": query,
                    "tool_calls": len(result.get("intermediate_steps", [])),
                    **kwargs
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent execution failed: {str(e)}"
            logger.error(error_msg)
            
            return AgentResponse(
                success=False,
                output="",
                intermediate_steps=[],
                execution_time=execution_time,
                agent_name=self.name,
                error=error_msg,
                metadata={"query": query, **kwargs}
            )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.tools],
            "model": config.llm.model_name,
            "max_iterations": self.config.max_iterations
        }
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class AgentFactory:
    """Factory for creating and managing agents."""
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type."""
        cls._agents[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> BaseAgent:
        """Create an agent of the specified type."""
        if agent_type not in cls._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._agents[agent_type]
        return agent_class(**kwargs)
    
    @classmethod
    def get_available_agents(cls) -> List[str]:
        """Get list of available agent types."""
        return list(cls._agents.keys())


# Export important classes
__all__ = ["BaseAgent", "AgentResponse", "AgentFactory"]