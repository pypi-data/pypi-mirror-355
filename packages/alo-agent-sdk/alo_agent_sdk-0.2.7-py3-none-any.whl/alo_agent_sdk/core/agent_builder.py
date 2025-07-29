"""
AgentBuilder class for the ALO Agent SDK.

This class simplifies the creation of A2A/MCP compliant FastAPI agents.
"""

import os
import asyncio
from typing import Optional, List, Dict, Callable, Any, Union
from functools import wraps

from fastapi import FastAPI
# Assuming python_a2a is installed and its models are accessible
# If python_a2a is part of the same monorepo/project at a different path,
# sys.path manipulation or relative imports might be needed depending on structure.
# For an SDK, it's typical to expect dependencies to be installed.
from alo_agent_sdk.alo_a2a.models.agent import AgentCard, AgentSkill
from alo_agent_sdk.alo_a2a.mcp.fastmcp import FastMCP, ToolDefinition as MCPToolDefinition # Renaming to avoid clash if we define our own
from alo_agent_sdk.alo_a2a.mcp.transport.fastapi import create_fastapi_app

from .registry_client import RegistryClient


class AgentBuilder:
    """
    Facilitates the creation of A2A/MCP compliant FastAPI agents.
    """

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        agent_base_url: Optional[str] = None,
        registry_url: Optional[str] = None,
        skills: Optional[List[AgentSkill]] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        default_input_modes: Optional[List[str]] = None,
        default_output_modes: Optional[List[str]] = None,
        provider: Optional[str] = None,
        documentation_url: Optional[str] = None,
        mcp_dependencies: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description

        self.agent_base_url = agent_base_url or os.getenv("ALO_AGENT_BASE_URL")
        if not self.agent_base_url:
            # In Cloud Run, PORT is set, and the service URL is auto-assigned.
            # For local dev, user might need to set this or we default.
            port = os.getenv("PORT", "8080")
            self.agent_base_url = f"http://localhost:{port}"
            print(f"Warning: ALO_AGENT_BASE_URL not set. Defaulting to {self.agent_base_url}. "
                  f"Ensure this is correct for registration if not running on Cloud Run with auto-assigned URL.")


        self.registry_url = registry_url or os.getenv("ALO_REGISTRY_URL")

        self._internal_skills_list: List[AgentSkill] = list(skills) if skills else []

        # Initialize FastMCP server which will hold the tools
        self.mcp_server = FastMCP(
            name=f"{self.name}-MCP", # MCP server might have a slightly different name
            version=self.version,
            description=f"MCP interface for {self.name}",
            dependencies=mcp_dependencies or []
        )

        # Initialize AgentCard
        # The URL in AgentCard should be the one where the agent is reachable.
        # This might be different from the MCP server's internal view if it's part of a larger app.
        # For standalone agents, agent_base_url is appropriate.
        self.agent_card = AgentCard(
            name=self.name,
            description=self.description,
            url=self.agent_base_url, # This is the publicly accessible URL of the agent service
            version=self.version,
            skills=self._internal_skills_list, # Start with pre-defined skills
            capabilities=capabilities or {"streaming": False, "pushNotifications": False, "mcp_tools": True},
            default_input_modes=default_input_modes or ["application/json"], # MCP usually uses JSON
            default_output_modes=default_output_modes or ["application/json"],
            provider=provider,
            documentation_url=documentation_url
        )
        
        self.fastapi_app: Optional[FastAPI] = None
        self.registry_client: Optional[RegistryClient] = RegistryClient() # Initialize client, it will be used if registry_url is set

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        skill_id: Optional[str] = None,
        skill_tags: Optional[List[str]] = None,
        skill_examples: Optional[List[str]] = None,
        skill_input_modes: Optional[List[str]] = None,
        skill_output_modes: Optional[List[str]] = None,
    ) -> Callable:
        """
        Decorator to register a function as an MCP tool and an AgentSkill.

        Args:
            name: Optional tool name (default: function name). Also used for AgentSkill name.
            description: Optional tool description (default: function docstring). Also for AgentSkill.
            skill_id: Optional custom ID for the AgentSkill.
            skill_tags: Optional list of tags for the AgentSkill.
            skill_examples: Optional list of examples for the AgentSkill.
            skill_input_modes: Optional input modes for the AgentSkill.
            skill_output_modes: Optional output modes for the AgentSkill.

        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or (func.__doc__ or "").strip()

            # Register with FastMCP server
            # The FastMCP @tool decorator itself handles parameter inspection.
            # We are essentially wrapping it to also create an AgentSkill.
            # We call the mcp_server.tool method directly here.
            # Note: FastMCP's tool decorator returns the original function,
            # so we need to call it and then return func.
            
            # This is a bit tricky because self.mcp_server.tool is a decorator itself.
            # We need to apply it to func.
            mcp_decorated_func = self.mcp_server.tool(name=tool_name, description=tool_description)(func)

            # Create and add AgentSkill to the AgentCard
            # If a skill with the same name already exists, we might want to update it or raise an error.
            # For now, let's assume new skill or overwrite.
            existing_skill_index = -1
            for i, s in enumerate(self._internal_skills_list):
                if s.name == tool_name:
                    existing_skill_index = i
                    break
            
            agent_skill = AgentSkill(
                id=skill_id or (self._internal_skills_list[existing_skill_index].id if existing_skill_index != -1 else None), # Retain ID if updating
                name=tool_name,
                description=tool_description,
                tags=skill_tags or [],
                examples=skill_examples or [],
                input_modes=skill_input_modes or self.agent_card.default_input_modes,
                output_modes=skill_output_modes or self.agent_card.default_output_modes
            )

            if existing_skill_index != -1:
                self._internal_skills_list[existing_skill_index] = agent_skill
            else:
                self._internal_skills_list.append(agent_skill)
            
            # Update the agent card's skills list directly
            self.agent_card.skills = self._internal_skills_list

            # Return the original function, as FastMCP's decorator does
            return mcp_decorated_func
        return decorator

    def get_fastapi_app(self) -> FastAPI:
        """
        Creates and returns the FastAPI application for this agent.
        The application will serve the MCP tools and the agent card.
        """
        if self.fastapi_app:
            return self.fastapi_app

        # Create the FastAPI app from the MCP server
        # This app will already have /tools, /resources, /metadata endpoints for MCP
        app = create_fastapi_app(self.mcp_server)

        # Add an endpoint to serve the agent's AgentCard
        @app.get("/agent.json", response_model=Dict[str, Any], tags=["Agent Information"])
        async def get_agent_card():
            return self.agent_card.to_dict()

        @app.get("/", include_in_schema=False) # Simple root redirect or info
        async def root():
            return {
                "message": f"Welcome to {self.name} v{self.version}",
                "agent_card_url": "/agent.json",
                "mcp_tools_url": "/tools" # from create_fastapi_app
            }
        
        @app.on_event("startup")
        async def startup_event():
            if self.registry_url and self.registry_client:
                # Ensure agent_base_url (and thus agent_card.url) is correctly set,
                # especially if it relies on dynamic port assignment or Cloud Run URL.
                # For Cloud Run, the actual service URL is known after deployment.
                # The agent_base_url passed or defaulted at __init__ should be the one to register.
                # If ALO_AGENT_BASE_URL env var is set by Cloud Run, it should be picked up.
                
                # Update agent_card.url if it was defaulted and a more specific one is now known
                # (e.g. from an environment variable set by the deployment environment)
                env_agent_url = os.getenv("ALO_AGENT_SERVICE_URL") # e.g. Cloud Run's K_SERVICE URL
                if env_agent_url:
                    self.agent_base_url = env_agent_url
                    self.agent_card.url = env_agent_url
                    print(f"Updated agent_card.url from ALO_AGENT_SERVICE_URL: {self.agent_card.url}")


                print(f"Attempting to register agent '{self.name}' with URL '{self.agent_card.url}' to registry at '{self.registry_url}'...")
                try:
                    await self.registry_client.register(self.registry_url, self.agent_card)
                    print(f"Agent '{self.name}' registered successfully.")
                    # Start heartbeat loop as a background task
                    # Ensure the loop itself handles exceptions gracefully to not crash the agent.
                    asyncio.create_task(
                        self.registry_client.start_heartbeat_loop(
                            registry_base_url=self.registry_url,
                            agent_url=self.agent_card.url # Use the registered URL
                        )
                    )
                except Exception as e:
                    print(f"Error during agent registration or starting heartbeat: {e}")
            else:
                print("Registry URL not configured (ALO_REGISTRY_URL). Skipping registration and heartbeat.")

        @app.on_event("shutdown")
        async def shutdown_event():
            if self.registry_client:
                await self.registry_client.close()
                print("Registry client closed.")

        self.fastapi_app = app
        return self.fastapi_app

if __name__ == '__main__':
    # Example usage (to be developed further)
    example_agent = AgentBuilder(
        name="MyExampleAgent",
        description="An agent built with ALO Agent SDK."
    )
    print(f"Agent Card URL: {example_agent.agent_card.url}")
    print(f"MCP Server Name: {example_agent.mcp_server.name}")
    # app = example_agent.get_fastapi_app()
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8080)
