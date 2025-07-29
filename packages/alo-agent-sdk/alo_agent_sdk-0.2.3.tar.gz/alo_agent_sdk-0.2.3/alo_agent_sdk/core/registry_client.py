"""
RegistryClient class for the ALO Agent SDK.

This client interacts with the Agent Registry Service.
"""

import httpx
import asyncio
import time
from typing import Optional, List, Dict, Any

# Assuming python_a2a.models.AgentCard is the structure we send for registration
# If the registry expects a different Pydantic model, we'd import/define that.
from alo_agent_sdk.alo_a2a.models.agent import AgentCard


class RegistryClientHttpError(Exception):
    """Custom exception for HTTP errors from the Registry Client."""
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Registry API request failed with status {status_code}: {detail}")


class RegistryClient:
    """
    Client for interacting with the Agent Registry Service.
    """
    DEFAULT_TIMEOUT = 10.0  # seconds

    def __init__(self, client: Optional[httpx.AsyncClient] = None, timeout: float = DEFAULT_TIMEOUT):
        """
        Initializes the RegistryClient.

        Args:
            client: An optional httpx.AsyncClient instance for custom configuration or testing.
            timeout: Default timeout for HTTP requests.
        """
        self._client = client
        self.timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the httpx client, creating one if it doesn't exist."""
        if self._client is None:
            # Create a new client if one wasn't provided
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Closes the underlying httpx.AsyncClient if it was created by this instance."""
        if self._client:
            await self._client.aclose()
            self._client = None # Allow re-creation if needed

    async def register(self, registry_base_url: str, agent_card: AgentCard) -> Dict[str, Any]:
        """
        Registers an agent with the Agent Registry Service.

        Args:
            registry_base_url: The base URL of the Agent Registry Service.
            agent_card: The AgentCard object of the agent to register.

        Returns:
            The JSON response from the registry service.

        Raises:
            RegistryClientHttpError: If the HTTP request fails.
            httpx.RequestError: For network errors.
        """
        client = await self._get_client()
        register_url = f"{registry_base_url.rstrip('/')}/registry/register"
        
        try:
            response = await client.post(register_url, json=agent_card.to_dict())
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise RegistryClientHttpError(status_code=e.response.status_code, detail=detail) from e
        # httpx.RequestError (like ConnectError, TimeoutException) will propagate

    async def send_heartbeat(self, registry_base_url: str, agent_url: str) -> Dict[str, Any]:
        """
        Sends a heartbeat signal for an agent to the Agent Registry Service.

        Args:
            registry_base_url: The base URL of the Agent Registry Service.
            agent_url: The URL of the agent sending the heartbeat.

        Returns:
            The JSON response from the registry service.

        Raises:
            RegistryClientHttpError: If the HTTP request fails.
            httpx.RequestError: For network errors.
        """
        client = await self._get_client()
        heartbeat_url = f"{registry_base_url.rstrip('/')}/registry/heartbeat"
        payload = {"url": agent_url}

        try:
            response = await client.post(heartbeat_url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise RegistryClientHttpError(status_code=e.response.status_code, detail=detail) from e

    async def get_agents(self, registry_base_url: str, skill_name: Optional[str] = None, skill_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of registered (and active) agents from the Agent Registry Service.
        Optionally filters by skill name or tags.

        Args:
            registry_base_url: The base URL of the Agent Registry Service.
            skill_name: Optional name of a skill to filter by.
            skill_tags: Optional list of tags to filter by (agents must have all tags).

        Returns:
            A list of agent card dictionaries.

        Raises:
            RegistryClientHttpError: If the HTTP request fails.
            httpx.RequestError: For network errors.
        """
        client = await self._get_client()
        agents_url = f"{registry_base_url.rstrip('/')}/registry/agents"
        
        params = {}
        if skill_name:
            params["skill_name"] = skill_name
        if skill_tags:
            params["skill_tags"] = ",".join(skill_tags) # Assuming API expects comma-separated string for multiple tags

        try:
            response = await client.get(agents_url, params=params)
            response.raise_for_status()
            return response.json() # Expects a list of agent card dicts
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise RegistryClientHttpError(status_code=e.response.status_code, detail=detail) from e
            
    async def start_heartbeat_loop(
        self, 
        registry_base_url: str, 
        agent_url: str, 
        interval_seconds: int = 60
    ):
        """
        Starts a loop that periodically sends heartbeats to the registry.
        This should typically be run as a background task (e.g., with asyncio.create_task).
        """
        print(f"Starting heartbeat loop for agent {agent_url} to registry {registry_base_url} every {interval_seconds}s.")
        while True:
            try:
                await self.send_heartbeat(registry_base_url, agent_url)
                # print(f"Heartbeat sent for {agent_url} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except RegistryClientHttpError as e:
                print(f"Error sending heartbeat for {agent_url}: {e.status_code} - {e.detail}")
            except httpx.RequestError as e:
                print(f"Network error sending heartbeat for {agent_url}: {e}")
            except Exception as e:
                print(f"Unexpected error in heartbeat loop for {agent_url}: {e}")
            
            await asyncio.sleep(interval_seconds)


if __name__ == '__main__':
    # Example usage (to be developed further with a running registry)
    async def main():
        # This requires a running Agent Registry Service at http://localhost:8001
        # And an AgentCard instance
        
        # Dummy AgentCard for testing
        dummy_card = AgentCard(
            name="TestAgentForClient",
            description="A test agent.",
            url="http://localhost:8088/testagent", # Agent's own URL
            version="1.0"
        )
        
        registry_client = RegistryClient()
        registry_service_url = "http://localhost:8001" # Assuming registry runs here

        try:
            print(f"Attempting to register agent '{dummy_card.name}' at {registry_service_url}...")
            # registration_response = await registry_client.register(registry_service_url, dummy_card)
            # print(f"Registration successful: {registration_response}")
            print("Example: Registration call commented out. Uncomment to test against a live registry.")

        except RegistryClientHttpError as e:
            print(f"Registry HTTP Error: {e.status_code} - {e.detail}")
        except httpx.RequestError as e:
            print(f"Registry Request Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            await registry_client.close()

    # To run this example:
    # 1. Ensure an Agent Registry Service (e.g., from alo_agent_sdk.registry_service.main) is running.
    # 2. Uncomment the registration call.
    # asyncio.run(main())
    pass
