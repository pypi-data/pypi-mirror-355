import os
from datetime import datetime
import uvicorn

# Ensure alo_agent_sdk is installed and import necessary components
# This will be available if requirements.sdk.txt (including alo-agent-sdk) is installed
from alo_agent_sdk.core import AgentBuilder
from alo_agent_sdk.alo_a2a.models.agent import AgentSkill # Optional: for explicit skill definition

# Determine the registry URL from environment variable, with a local default
ALO_REGISTRY_URL = os.getenv("ALO_REGISTRY_URL", "http://localhost:8001")

# Determine the agent's own base URL.
# For Cloud Run, this is typically provided by K_SERVICE and PORT.
# For local, we construct it. AgentBuilder has some internal defaults too.
PORT = os.getenv("PORT", "8080")
ALO_AGENT_BASE_URL = os.getenv("ALO_AGENT_SERVICE_URL") # Cloud Run might set this (e.g. K_SERVICE)
if not ALO_AGENT_BASE_URL:
    # Default for local development if not set by environment (e.g. Docker Compose)
    # Ensure this matches how the agent is accessible from the registry and orchestrator
    ALO_AGENT_BASE_URL = f"http://localhost:{PORT}" 
    # For Docker Compose, this might be http://time_agent:{PORT} if other services resolve by container name

time_agent = AgentBuilder(
    name="TimeAgent",
    version="0.1.0",
    description="A simple agent that provides the current date and time.",
    agent_base_url=ALO_AGENT_BASE_URL, # Explicitly pass the determined base URL
    registry_url=ALO_REGISTRY_URL,
    skills=[
        AgentSkill(name="time_service", description="Provides current time information.")
    ]
)

@time_agent.tool(
    name="get_current_time", # Explicit tool name
    description="Retrieves the current server date and time in ISO format.",
    skill_id="time_service" # Associate with the 'time_service' skill
)
async def get_current_time() -> str:
    """
    Returns the current date and time as an ISO 8601 formatted string.
    """
    now_iso = datetime.now().isoformat()
    print(f"TimeAgent: Executing get_current_time. Returning: {now_iso}")
    return now_iso

# Get the FastAPI app instance from the builder
app = time_agent.get_fastapi_app()

# For local execution (mainly for testing outside Docker, Uvicorn is run by Docker CMD)
if __name__ == "__main__":
    print(f"Starting TimeAgent locally on {ALO_AGENT_BASE_URL}")
    print(f"Attempting to register with registry at {ALO_REGISTRY_URL}")
    # Note: For local registration to work, the registry service must be running
    # and accessible at ALO_REGISTRY_URL.
    # The agent_base_url must also be reachable by the registry.
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
