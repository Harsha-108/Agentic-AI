"""
LangSmith Configuration and Utilities
Centralized configuration for LangSmith tracing across the multi-agent system
"""

import os
import logging
from typing import Optional, Dict, Any
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Centralized LangSmith configuration and utilities"""
    
    def __init__(self):
        self.enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project = os.getenv("LANGCHAIN_PROJECT", "multi-agent-poc-backend")
        self.client: Optional[Client] = None
        
        if self.enabled and self.api_key:
            try:
                self.client = Client(api_key=self.api_key)
                logger.info(f"LangSmith initialized for project: {self.project}")
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client: {e}")
                self.enabled = False
        elif self.enabled:
            logger.warning("LangSmith tracing enabled but no API key provided")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled and properly configured"""
        return self.enabled and self.client is not None
    
    def get_client(self) -> Optional[Client]:
        """Get the LangSmith client instance"""
        return self.client
    
    def log_agent_interaction(
        self, 
        agent_name: str, 
        user_input: str, 
        agent_response: str,
        confidence: float = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Log an agent interaction to LangSmith"""
        if not self.is_enabled():
            return
        
        try:
            run_data = {
                "name": f"{agent_name}_interaction",
                "run_type": "chain",
                "inputs": {"user_input": user_input},
                "outputs": {"agent_response": agent_response},
                "extra": {
                    "agent": agent_name,
                    "confidence": confidence,
                    "project": self.project,
                    **(metadata or {})
                }
            }
            
            self.client.create_run(**run_data)
            logger.debug(f"Logged {agent_name} interaction to LangSmith")
            
        except Exception as e:
            logger.warning(f"Failed to log interaction to LangSmith: {e}")
    
    def log_routing_decision(
        self,
        message: str,
        selected_agent: str,
        confidence: float,
        routing_method: str,
        available_agents: list
    ) -> None:
        """Log a routing decision to LangSmith"""
        if not self.is_enabled():
            return
        
        try:
            run_data = {
                "name": "message_routing",
                "run_type": "chain",
                "inputs": {
                    "message": message,
                    "available_agents": available_agents
                },
                "outputs": {
                    "selected_agent": selected_agent,
                    "confidence": confidence,
                    "routing_method": routing_method
                },
                "extra": {
                    "component": "router",
                    "project": self.project
                }
            }
            
            self.client.create_run(**run_data)
            logger.debug(f"Logged routing decision to LangSmith: {selected_agent}")
            
        except Exception as e:
            logger.warning(f"Failed to log routing decision to LangSmith: {e}")
    
    def log_tool_execution(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Any,
        execution_time: float = None,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log tool execution to LangSmith"""
        if not self.is_enabled():
            return
        
        try:
            run_data = {
                "name": f"tool_{tool_name}",
                "run_type": "tool",
                "inputs": inputs,
                "outputs": outputs if success else None,
                "extra": {
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "success": success,
                    "project": self.project
                }
            }
            
            if error:
                run_data["error"] = error
            
            self.client.create_run(**run_data)
            logger.debug(f"Logged tool execution to LangSmith: {tool_name}")
            
        except Exception as e:
            logger.warning(f"Failed to log tool execution to LangSmith: {e}")
    
    def create_dataset(self, name: str, description: str = None) -> Optional[str]:
        """Create a dataset for evaluation"""
        if not self.is_enabled():
            return None
        
        try:
            dataset = self.client.create_dataset(
                dataset_name=name,
                description=description or f"Dataset for {self.project}"
            )
            logger.info(f"Created LangSmith dataset: {name}")
            return dataset.id
        except Exception as e:
            logger.error(f"Failed to create LangSmith dataset: {e}")
            return None
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics from LangSmith"""
        if not self.is_enabled():
            return {}
        
        try:
            # This would need to be implemented based on LangSmith API
            # Currently returning basic info
            return {
                "project": self.project,
                "tracing_enabled": True,
                "client_available": self.client is not None
            }
        except Exception as e:
            logger.error(f"Failed to get project stats: {e}")
            return {}


# Global instance
langsmith_config = LangSmithConfig()


def get_langsmith_config() -> LangSmithConfig:
    """Get the global LangSmith configuration instance"""
    return langsmith_config


def is_tracing_enabled() -> bool:
    """Quick check if tracing is enabled"""
    return langsmith_config.is_enabled()