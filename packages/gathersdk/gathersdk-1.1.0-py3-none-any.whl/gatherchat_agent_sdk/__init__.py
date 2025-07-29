"""
GatherChat Agent SDK

A Python SDK for building agents that integrate with GatherChat.
"""

from .agent import (
    BaseAgent,
    AgentContext,
    UserContext,
    ChatContext,
    MessageContext,
    AgentResponse,
    AgentError
)
from .client import AgentClient, run_agent
from .auth import SimpleAuth
from .simple_agent import Agent

__version__ = "1.1.0"

__all__ = [
    # Simple interface (pydantic-ai style)
    "Agent",
    
    # Core classes
    "BaseAgent",
    "AgentClient",
    "SimpleAuth",
    
    # Context models
    "AgentContext",
    "UserContext", 
    "ChatContext",
    "MessageContext",
    
    # Helper classes
    "AgentResponse",
    "AgentError",
    
    # Convenience functions
    "run_agent"
]