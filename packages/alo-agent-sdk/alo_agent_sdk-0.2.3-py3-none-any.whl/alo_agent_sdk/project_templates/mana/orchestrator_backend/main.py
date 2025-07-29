import os
import uvicorn
from fastapi import FastAPI, HTTPException
import logging

# Assuming client.py is in the same directory and provides ApplicationAgentClient
from client import ApplicationAgentClient, logger as client_logger

# Configure basic logging for the orchestrator
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - ORCHESTRATOR - %(message)s')
logger = logging.getLogger(__name__)
# You might want to set the client_logger's level or handlers differently if needed
# For now, they share the basicConfig if client.py is imported.

app = FastAPI(
    title="Mana Orchestrator Service",
    description="Backend orchestrator that calls the TimeAgent via the agent ecosystem.",
    version="0.1.0",
)

# Determine the registry URL from environment variable, with a local default
ALO_REGISTRY_URL = os.getenv("ALO_REGISTRY_URL", "http://localhost:8001")
PORT = os.getenv("PORT", "8000") # Orchestrator's own port

if not ALO_REGISTRY_URL:
    logger.critical("ALO_REGISTRY_URL environment variable not set. Orchestrator may not function correctly.")
    # Depending on strictness, you might raise an error here or allow it to run with warnings.

# Initialize the agent service client
# This client will be used by the API endpoints to interact with agents.
agent_service_client = ApplicationAgentClient(registry_url=ALO_REGISTRY_URL)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Mana Orchestrator Service starting up on port {PORT}.")
    logger.info(f"Using Agent Registry Service at: {ALO_REGISTRY_URL}")
    # You could add a health check to the registry here if desired

@app.get("/api/get_current_time", tags=["Time Service"])
async def get_time_from_agent_endpoint():
    """
    API endpoint to get the current time by orchestrating a call to the TimeAgent.
    """
    logger.info("Received request for /api/get_current_time")
    try:
        # Use the ApplicationAgentClient to find the TimeAgent (via its skill)
        # and call its 'get_current_time' tool.
        # The TimeAgent in mana/time_agent/main.py is defined with skill "time_service"
        # and tool "get_current_time".
        time_data = await agent_service_client.execute_task_with_fallbacks(
            tool_name="get_current_time",
            payload={},  # No payload needed for this specific tool
            skill_name="time_service" 
        )

        if time_data is None:
            logger.error("Failed to get time from TimeAgent: No result returned from client.")
            raise HTTPException(
                status_code=503, 
                detail="Time service is currently unavailable or no TimeAgent found."
            )
        
        # The 'get_current_time' tool in TimeAgent returns the ISO string directly.
        # If it returned a dict like {"time": "iso_string"}, access it: time_data.get("time")
        logger.info(f"Successfully retrieved time from agent: {time_data}")
        return {"current_time_from_agent": time_data}

    except HTTPException:
        raise # Re-raise HTTPException if it's already one (e.g. from client logic if adapted)
    except Exception as e:
        logger.exception(f"An unexpected error occurred while trying to get time from agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error in orchestrator: {str(e)}"
        )

@app.get("/health", tags=["Management"])
async def health_check():
    """Performs a health check of the orchestrator service."""
    return {"status": "healthy", "service": "Mana Orchestrator"}

if __name__ == "__main__":
    # This is for local development. In Docker, Uvicorn is started by the CMD.
    print(f"Starting Mana Orchestrator locally on http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
