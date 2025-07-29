import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import asyncio
from typing import List, Dict, Any, Optional

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions with Retry Logic ---

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)),
    reraise=True # Reraise the exception if all retries fail
)
async def discover_agents_from_registry(registry_url: str, skill_name: Optional[str] = None, skill_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Discovers agents from the registry service with retry logic for network issues.
    """
    params = {}
    if skill_name:
        params["skill_name"] = skill_name
    if skill_tags:
        params["skill_tags"] = skill_tags # FastAPI handles multiple query params with same name

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.info(f"Discovering agents from {registry_url} with params: {params}")
            response = await client.get(f"{registry_url}/registry/agents", params=params)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            agents = response.json()
            logger.info(f"Discovered {len(agents)} agent(s).")
            return agents
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP error {exc.response.status_code} from registry {exc.request.url!r}: {exc.response.text}")
            # For specific client errors (4xx), we might not want to retry,
            # but tenacity is configured to retry only on network/timeout by default here.
            # If it's a 404 (no agents found with criteria), it's not an "error" in the retry sense.
            if exc.response.status_code == 404: # Or based on how registry signals "no agents found"
                 logger.info(f"No agents found matching criteria at registry {exc.request.url!r}.")
                 return [] # Return empty list if no agents match
            raise # Reraise other HTTPStatusErrors
        except httpx.TimeoutException:
            logger.warning(f"Timeout connecting to registry: {registry_url}")
            raise
        except httpx.RequestError as exc: # Covers NetworkError, ConnectError etc.
            logger.warning(f"Network error connecting to registry {exc.request.url!r}: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error discovering agents: {exc}")
            raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError, httpx.HTTPStatusError)), # Retry on 5xx errors too
    reraise=True
)
async def call_agent_tool(agent_base_url: str, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls a tool on a specific agent with retry logic.
    Retries on timeouts, network errors, and 5xx HTTP errors from the agent.
    """
    tool_url = f"{agent_base_url.rstrip('/')}/tools/{tool_name}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            logger.info(f"Calling tool '{tool_name}' on agent {agent_base_url} with payload: {payload}")
            response = await client.post(tool_url, json=payload)
            
            # Check for 5xx errors to retry, otherwise raise for 4xx immediately (or let it pass if 2xx)
            if 500 <= response.status_code < 600:
                response.raise_for_status() # This will trigger retry for 5xx

            response.raise_for_status() # For other errors (e.g. 4xx) that shouldn't be retried by this specific config
                                        # or to get details if it's a non-5xx error after retries.
            
            result = response.json()
            logger.info(f"Tool '{tool_name}' on agent {agent_base_url} executed successfully.")
            return result
        except httpx.HTTPStatusError as exc:
            # Log specific details for HTTP errors
            logger.error(f"HTTP error {exc.response.status_code} from agent {exc.request.url!r} calling tool '{tool_name}': {exc.response.text}")
            if 500 <= exc.response.status_code < 600:
                 raise # Reraise to trigger tenacity retry for 5xx
            # For 4xx errors, it will be raised after this block if not retried by tenacity config
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout calling tool '{tool_name}' on agent {agent_base_url}")
            raise
        except httpx.RequestError as exc:
            logger.warning(f"Network error calling agent {exc.request.url!r}: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error calling agent tool: {exc}")
            raise

# --- Main Application Client Class ---

class ApplicationAgentClient:
    def __init__(self, registry_url: str):
        if not registry_url:
            raise ValueError("Registry URL must be provided.")
        self.registry_url = registry_url
        logger.info(f"ApplicationAgentClient initialized with registry URL: {self.registry_url}")
        # In a more advanced scenario, circuit breakers could be initialized here per agent/service.

    async def find_available_agents(self, skill_name: Optional[str] = None, skill_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Finds agents based on skill name and/or tags.
        Returns a list of agent card dictionaries.
        """
        try:
            agents = await discover_agents_from_registry(self.registry_url, skill_name, skill_tags)
            return agents
        except Exception as e:
            logger.error(f"Failed to discover agents for skill '{skill_name}' / tags '{skill_tags}': {e}")
            return [] # Return empty list on failure to allow application to decide fallback

    async def execute_task_with_fallbacks(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        skill_name: Optional[str] = None, # To discover agents for this skill
        skill_tags: Optional[List[str]] = None,
        preferred_agent_name: Optional[str] = None # Optionally prefer a specific agent
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a tool by finding suitable agents and trying them sequentially
        if failures occur.
        """
        logger.info(f"Attempting to execute tool '{tool_name}' for skill '{skill_name}' / tags '{skill_tags}'")
        
        try:
            candidate_agents = await self.find_available_agents(skill_name, skill_tags)
        except Exception as e:
            logger.error(f"Critical error during agent discovery for tool '{tool_name}': {e}. Aborting task.")
            return None

        if not candidate_agents:
            logger.warning(f"No agents found for skill '{skill_name}' / tags '{skill_tags}' to execute tool '{tool_name}'.")
            return None

        # Sort agents: preferred first, then by some other metric if available (e.g. version, custom metadata)
        if preferred_agent_name:
            candidate_agents.sort(key=lambda ag: ag.get("name") == preferred_agent_name, reverse=True)

        last_exception: Optional[Exception] = None
        
        for agent_card in candidate_agents:
            agent_name = agent_card.get("name", "UnknownAgent")
            agent_url = agent_card.get("url")

            if not agent_url:
                logger.warning(f"Agent '{agent_name}' has no URL in its card. Skipping.")
                continue

            logger.info(f"Attempting tool '{tool_name}' on agent '{agent_name}' at {agent_url}")
            try:
                # Here, one might integrate a circuit breaker per agent_url
                # For simplicity, direct call for now.
                result = await call_agent_tool(agent_url, tool_name, payload)
                logger.info(f"Successfully executed tool '{tool_name}' on agent '{agent_name}'.")
                return result  # Success!
            except Exception as e:
                logger.warning(f"Failed to execute tool '{tool_name}' on agent '{agent_name}' ({agent_url}): {e}")
                last_exception = e
                # Continue to the next agent if this one failed
        
        logger.error(f"All suitable agents failed to execute tool '{tool_name}'. Last error: {last_exception}")
        # Optionally, re-raise last_exception or a custom aggregated error
        # raise TaskExecutionFailedError("All agents failed", last_exception) from last_exception
        return None


# --- Example Usage (Illustrative) ---
# This part can be removed if this file is purely a library module for the orchestrator
async def main_example():
    # IMPORTANT: Replace with your actual registry URL
    REGISTRY_SERVICE_URL = "http://localhost:8001" # Example, use your deployed registry URL

    client = ApplicationAgentClient(registry_url=REGISTRY_SERVICE_URL)

    # Example 1: Discover agents with a specific skill
    logger.info("\n--- Example 1: Discovering 'calculator' agents ---")
    calculator_agents = await client.find_available_agents(skill_name="calculator")
    if calculator_agents:
        logger.info(f"Found calculator agents: {[ag.get('name') for ag in calculator_agents]}")
        for agent in calculator_agents:
            logger.info(f"  - {agent.get('name')}: {agent.get('url')}, version {agent.get('version')}")
            logger.info(f"    Skills: {[s.get('name') for s in agent.get('skills', [])]}")
    else:
        logger.info("No 'calculator' agents found.")

    # Example 2: Execute a 'sum' tool, expecting it from an agent with 'calculator' skill
    logger.info("\n--- Example 2: Executing 'sum' tool ---")
    sum_payload = {"a": 10, "b": 5}
    sum_result = await client.execute_task_with_fallbacks(
        tool_name="sum",
        payload=sum_payload,
        skill_name="calculator" # The client will look for agents with this skill
    )

    if sum_result:
        logger.info(f"Result of sum(10, 5): {sum_result}")
    else:
        logger.error("Failed to execute 'sum' tool.")

    # Example 3: Execute a non-existent tool or on non-existent agent to see error handling
    logger.info("\n--- Example 3: Executing a non-existent tool ---")
    non_existent_payload = {"data": "test"}
    error_result = await client.execute_task_with_fallbacks(
        tool_name="non_existent_tool",
        payload=non_existent_payload,
        skill_name="any_skill"
    )
    if error_result is None:
        logger.info("Correctly handled non-existent tool execution (returned None).")

if __name__ == "__main__":
    # This example requires a running ALO Agent Registry and at least one agent
    # registered with a "calculator" skill and a "sum" tool.
    # You can run the example_registry_deploy and example_agent from the alo_agent_sdk
    # after modifying the example_agent to have a "calculator" skill and "sum" tool.

    # To run this example:
    # 1. Ensure your ALO Agent Registry is running (e.g., on http://localhost:8001)
    # 2. Ensure an agent with a 'calculator' skill and 'sum' tool is running and registered.
    #    (e.g., modify alo_agent_sdk/examples/example_agent/main.py)
    # 3. Update REGISTRY_SERVICE_URL if needed.
    # 4. Run `python robust_client.py`
    
    logger.info("Starting robust client example (requires running registry and agents)...")
    asyncio.run(main_example())
