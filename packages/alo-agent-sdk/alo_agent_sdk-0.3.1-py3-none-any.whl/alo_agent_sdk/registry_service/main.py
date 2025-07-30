"""
Main application file for the Agent Registry Service.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import HttpUrl

from .models import (
    AgentRegistrationData, 
    HeartbeatRequest, 
    AgentInfo, 
    RegistryAgentResponse,
    SimpleResponse
)

app = FastAPI(
    title="ALO Agent Registry Service",
    description="A FastAPI-based registry for ALO agents.",
    version="0.1.0", # Consider making this dynamic from pyproject.toml or SDK version
    docs_url="/docs",
    redoc_url="/redoc"
)

# In-memory storage (for initial implementation)
# Key: agent_url (str representation of HttpUrl for dict key)
# Value: AgentInfo instance
registered_agents: Dict[str, AgentInfo] = {}

# Configuration for agent pruning
PRUNE_INTERVAL_SECONDS: int = 60 * 5 # Prune every 5 minutes
MAX_AGENT_INACTIVITY_SECONDS: int = 60 * 15 # Agent considered inactive after 15 minutes


@app.get("/health", tags=["Management"], response_model=SimpleResponse)
async def health_check():
    """Performs a health check of the registry service."""
    return SimpleResponse(success=True, message="ALO Agent Registry Service is healthy.")

@app.post("/registry/register", tags=["Registry"], response_model=SimpleResponse)
async def register_agent(agent_data: AgentRegistrationData):
    """
    Registers an agent with the registry.
    If an agent with the same URL already exists, its information will be updated.
    """
    agent_url_str = str(agent_data.url)
    registered_agents[agent_url_str] = AgentInfo(agent_card=agent_data, last_seen=time.time())
    print(f"Agent '{agent_data.name}' registered/updated from URL: {agent_url_str}")
    return SimpleResponse(success=True, message=f"Agent '{agent_data.name}' registered successfully.")

@app.post("/registry/heartbeat", tags=["Registry"], response_model=SimpleResponse)
async def agent_heartbeat(request: HeartbeatRequest):
    """
    Receives a heartbeat from an agent, updating its last_seen timestamp.
    """
    agent_url_str = str(request.url)
    if agent_url_str in registered_agents:
        registered_agents[agent_url_str].last_seen = time.time()
        # print(f"Heartbeat received from: {agent_url_str}")
        return SimpleResponse(success=True, message="Heartbeat acknowledged.")
    else:
        # Optionally, allow heartbeat to also register a new agent if not found.
        # For now, we require agents to be registered first.
        raise HTTPException(
            status_code=404, 
            detail=f"Agent with URL '{agent_url_str}' not found. Please register the agent first."
        )

@app.get("/registry/agents", tags=["Registry"], response_model=List[RegistryAgentResponse])
async def list_agents(
    skill_name: Optional[str] = Query(None, description="Filter agents by skill name."),
    # For skill_tags, FastAPI Query will handle comma-separated list if type is List[str]
    # However, client needs to send it as ?skill_tags=tag1&skill_tags=tag2 or ensure proper parsing if comma-separated.
    # Let's assume client sends multiple skill_tags parameters or we adjust client/server for comma-separated.
    # For simplicity, let's use Query(None) which allows multiple values for skill_tags.
    skill_tags: Optional[List[str]] = Query(None, description="Filter agents by skill tags (provide multiple times for multiple tags, e.g., ?skill_tags=tag1&skill_tags=tag2).")
):
    """
    Lists active agents, optionally filtering by skill name and/or tags.
    An agent is considered active if its last_seen timestamp is within MAX_AGENT_INACTIVITY_SECONDS.
    """
    current_time = time.time()
    active_agents_response: List[RegistryAgentResponse] = []

    for agent_url, agent_info in registered_agents.items():
        if (current_time - agent_info.last_seen) <= MAX_AGENT_INACTIVITY_SECONDS:
            # Agent is active, now check filters
            agent_card_data = agent_info.agent_card

            # Filter by skill_name
            if skill_name:
                if not any(skill.get("name") == skill_name for skill in agent_card_data.skills):
                    continue # Skip this agent if skill_name doesn't match

            # Filter by skill_tags (agent must have ALL specified tags)
            if skill_tags:
                agent_skill_tags_flat = set()
                for skill in agent_card_data.skills:
                    for tag in skill.get("tags", []):
                        agent_skill_tags_flat.add(tag)
                
                if not set(skill_tags).issubset(agent_skill_tags_flat):
                    continue # Skip this agent if not all skill_tags are present

            active_agents_response.append(RegistryAgentResponse(**agent_card_data.model_dump()))
            
    return active_agents_response

@app.delete("/registry/unregister", tags=["Registry"], response_model=SimpleResponse)
async def unregister_agent(agent_url: HttpUrl):
    """
    Unregisters an agent from the registry.
    """
    agent_url_str = str(agent_url)
    if agent_url_str in registered_agents:
        del registered_agents[agent_url_str]
        print(f"Agent at URL '{agent_url_str}' unregistered.")
        return SimpleResponse(success=True, message=f"Agent at URL '{agent_url_str}' unregistered successfully.")
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Agent with URL '{agent_url_str}' not found."
        )

async def prune_inactive_agents_task():
    """
    Periodically checks for inactive agents and removes them from the registry.
    This task runs in the background.
    """
    while True:
        await asyncio.sleep(PRUNE_INTERVAL_SECONDS)
        current_time = time.time()
        agents_to_prune = []
        
        print(f"Registry: Running prune task at {time.strftime('%Y-%m-%d %H:%M:%S')}. {len(registered_agents)} agents currently registered.")
        for agent_url, agent_info in registered_agents.items():
            if (current_time - agent_info.last_seen) > MAX_AGENT_INACTIVITY_SECONDS:
                agents_to_prune.append(agent_url)
        
        if agents_to_prune:
            for agent_url_to_prune in agents_to_prune:
                if agent_url_to_prune in registered_agents: # Check again in case of race condition (unlikely here)
                    agent_name = registered_agents[agent_url_to_prune].agent_card.name
                    del registered_agents[agent_url_to_prune]
                    print(f"Pruned inactive agent: '{agent_name}' from URL {agent_url_to_prune}")
            print(f"Pruning complete. Removed {len(agents_to_prune)} inactive agent(s).")
        else:
            print("Registry: No inactive agents to prune.")


@app.on_event("startup")
async def startup_event():
    """
    Event handler for application startup.
    Starts the background task for pruning inactive agents.
    """
    print("ALO Agent Registry Service starting up...")
    asyncio.create_task(prune_inactive_agents_task())
    print("Pruning task for inactive agents scheduled.")

if __name__ == "__main__":
    # For local testing of the registry service
    import uvicorn
    print(f"Starting ALO Agent Registry Service locally on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
