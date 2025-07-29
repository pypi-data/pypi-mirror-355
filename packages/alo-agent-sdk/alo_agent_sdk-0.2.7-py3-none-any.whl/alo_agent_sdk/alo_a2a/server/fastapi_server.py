"""
FastAPI server runner for A2A agents.
This module provides a way to run an A2AServer instance (which should set up its own FastAPI routes)
using Uvicorn.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

# Assuming BaseA2AServer is correctly importable
from .base import BaseA2AServer
# For the test mock agent in if __name__ == "__main__":
from ..models.message import Message, MessageRole # Relative import
from ..models.conversation import Conversation # Relative import
from ..models.content import TextContent # Relative import


def create_fastapi_app(agent: BaseA2AServer) -> FastAPI:
    """
    Create a FastAPI application and sets up routes using the provided agent.
    
    Args:
        agent: The A2A agent server instance (expected to have a setup_routes method)
        
    Returns:
        A FastAPI application
    """
    # Try to get agent card attributes safely
    agent_card = getattr(agent, 'agent_card', None)
    app_title = "A2A Agent (FastAPI)"
    app_description = "A2A Protocol Server using FastAPI"
    app_version = "1.0.0"

    if agent_card:
        app_title = getattr(agent_card, 'name', app_title) + " (FastAPI)"
        app_description = getattr(agent_card, 'description', app_description)
        app_version = getattr(agent_card, 'version', app_version)
        
    app = FastAPI(
        title=app_title,
        description=app_description,
        version=app_version
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # The agent itself is responsible for setting up its routes
    if hasattr(agent, 'setup_routes') and callable(agent.setup_routes):
        agent.setup_routes(app) # type: ignore[operator] # Pylance might complain if agent type is too generic
    else:
        print(f"Warning: The provided agent of type {type(agent).__name__} does not have a callable 'setup_routes' method. No agent-specific routes will be added.")

    return app


def run_fastapi_server(
    agent: BaseA2AServer,
    host: str = "0.0.0.0",
    port: int = 5000,
    log_level: str = "info"
) -> None:
    """
    Run an A2A agent as a FastAPI/Uvicorn server.
    
    Args:
        agent: The A2A agent server
        host: Host to bind to
        port: Port to listen on
        log_level: Uvicorn log level
    """
    app = create_fastapi_app(agent)
    print(f"Starting A2A FastAPI server on http://{host}:{port}")
    if hasattr(app, 'docs_url') and app.docs_url: # Check if docs_url is not None
         print(f"API documentation available at http://{host}:{port}{app.docs_url}")
    if hasattr(app, 'redoc_url') and app.redoc_url: # Check if redoc_url is not None
         print(f"Alternate API documentation available at http://{host}:{port}{app.redoc_url}")

    if hasattr(agent, '_use_google_a2a'):
        google_compat = getattr(agent, '_use_google_a2a', False)
        print(f"Google A2A compatibility hint: {'Enabled' if google_compat else 'Disabled'}")
        
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    # This is a placeholder for testing the server runner.
    # A real agent (like A2AServer from a2a_server.py) would be instantiated here.
    
    # Minimal AgentCard-like structure for testing create_fastapi_app
    class MockAgentCard:
        def __init__(self, name="Mock Agent", description="A mock agent.", version="0.1.0"):
            self.name = name
            self.description = description
            self.version = version
            self.capabilities: Dict[str, Any] = {} # For compatibility if accessed

    class MockServerForRunner(BaseA2AServer):
        def __init__(self, agent_id="mock_runner_agent", agent_name="MockRunnerAgent"):
            super().__init__(agent_id=agent_id) 
            self.agent_name = agent_name
            self.agent_card = MockAgentCard(name=agent_name) # Attach a mock card
            self._use_google_a2a = False # Example attribute

        def setup_routes(self, app: FastAPI):
            @app.get("/test-mock-runner")
            async def test_route():
                return {"message": f"Hello from {self.agent_name}"}
            print(f"MockServerForRunner '{self.agent_name}' routes set up on /test-mock-runner.")

        # --- Minimal BaseA2AServer abstract method implementations ---
        async def handle_message(self, message: Message) -> Message:
            # This method is abstract in BaseA2AServer
            print(f"MockServerForRunner received message: {message.content}")
            return Message(content=TextContent(text="Mock response"), role=MessageRole.ASSISTANT)

        async def handle_conversation(self, conversation: Conversation) -> Conversation:
            # This method is abstract in BaseA2AServer
            print(f"MockServerForRunner received conversation with {len(conversation.messages)} messages.")
            if conversation.messages:
                await self.handle_message(conversation.messages[-1])
            return conversation
        
        def get_metadata(self) -> Dict[str, Any]:
            # This method is abstract in BaseA2AServer
            return {"name": self.agent_name, "mock_metadata": True}

    print("Creating MockServerForRunner instance...")
    mock_agent_instance = MockServerForRunner()
    
    print(f"Running FastAPI server with {mock_agent_instance.agent_name} on port 8001...")
    run_fastapi_server(mock_agent_instance, port=8001)
