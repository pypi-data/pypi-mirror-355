from typing import Optional, Literal
from pydantic import BaseModel, Field

# This model is a simplified version for LLM interaction.
# The full configuration options are in alo_agent_sdk.alo_a2a.mcp.config_models
# The LLM will help populate these fields, which can then be used to
# programmatically call `alo-sdk mcp configure` or directly update mcp_servers.json.

class MCPClientAuthDetails(BaseModel):
    auth_type: Optional[Literal["none", "basic", "bearer", "api_key"]] = Field("none", description="Authentication method.")
    auth_source: Optional[Literal["env", "file", "direct"]] = Field("env", description="Where to load credentials from. 'direct' implies providing them now (less secure, for testing).")
    
    # For basic auth
    username: Optional[str] = Field(None, description="Username for basic authentication.")
    password: Optional[str] = Field(None, description="Password for basic authentication (if auth_source is 'direct').") # Consider security implications
    username_env_var: Optional[str] = Field(None, description="Environment variable for basic auth username.")
    password_env_var: Optional[str] = Field(None, description="Environment variable for basic auth password.")
    username_file_path: Optional[str] = Field(None, description="File path for basic auth username.")
    password_file_path: Optional[str] = Field(None, description="File path for basic auth password.")

    # For bearer/api_key auth
    token: Optional[str] = Field(None, description="Token/API key (if auth_source is 'direct').") # Consider security implications
    token_env_var: Optional[str] = Field(None, description="Environment variable for bearer token or API key.")
    token_file_path: Optional[str] = Field(None, description="File path for bearer token or API key.")
    
    # For API key specific
    apikey_name: Optional[str] = Field("X-API-Key", description="Name of the header or query parameter for API key.")
    apikey_location: Optional[Literal["header", "query"]] = Field("header", description="Where the API key is sent.")


class MCPClientSetup(BaseModel):
    server_name: str = Field(..., description="A unique name for this MCP server configuration (e.g., 'WeatherService', 'MyLocalUtilityAgent').")
    server_type: Literal["remote", "local"] = Field(..., description="Type of the MCP server.")
    
    # For remote servers
    url: Optional[str] = Field(None, description="The base URL of the remote MCP server (e.g., 'http://localhost:8001', 'https://api.example.com/mcp'). Required if server_type is 'remote'.")
    
    # For local servers (simplified for LLM, full config is more complex)
    project_path: Optional[str] = Field(None, description="Path to the local server's project directory. Required if server_type is 'local'.")
    run_command: Optional[str] = Field(None, description="Command to start the local server if not using Docker Compose (e.g., 'python main.py').")
    port: Optional[int] = Field(None, description="Port the local server listens on. Required if server_type is 'local'.")
    # Docker/compose options are omitted for this initial LLM-guided setup for simplicity.
    # Users can refine these using the full `alo-sdk mcp configure` CLI.

    authentication: MCPClientAuthDetails = Field(default_factory=MCPClientAuthDetails, description="Authentication details for connecting to the MCP server.")
    description: Optional[str] = Field(None, description="Optional description of this MCP server configuration.")
