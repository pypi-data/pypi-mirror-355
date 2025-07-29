"""
Pydantic models for the Agent Registry Service.
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, HttpUrl, Field

# We expect to receive a full AgentCard dictionary for registration.
# python_a2a.models.AgentCard could be used for validation if the dependency is managed,
# but for the registry API, accepting a Dict and validating key fields might be more robust
# if we don't want the registry service to have a hard dependency on the exact AgentCard model version.
# For now, let's assume the client (AgentBuilder) sends a valid AgentCard.to_dict().

class AgentRegistrationData(BaseModel):
    """
    Data model for agent registration. Expects a dictionary representation of an AgentCard.
    The `url` field from the AgentCard will be used as the primary key.
    """
    name: str
    url: HttpUrl # Crucial for identifying the agent
    description: Optional[str] = None
    version: Optional[str] = "0.1.0"
    skills: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Add other fields from AgentCard as needed for validation or direct use.
    # For simplicity, we'll mostly rely on the client sending a complete AgentCard dict.

    class Config:
        extra = 'allow' # Allow other fields from AgentCard

class HeartbeatRequest(BaseModel):
    """
    Data model for agent heartbeat.
    """
    url: HttpUrl # URL of the agent sending the heartbeat

class AgentInfo(BaseModel):
    """
    Internal representation of a registered agent in the registry.
    """
    agent_card: AgentRegistrationData # Stores the (potentially validated) card data
    last_seen: float = Field(default_factory=time.time)

class RegistryAgentResponse(AgentRegistrationData):
    """
    Data model for responding to /registry/agents queries.
    Essentially the same as AgentRegistrationData, ensuring we return consistent agent info.
    """
    pass

class SimpleResponse(BaseModel):
    """
    A simple success/failure response model.
    """
    success: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
