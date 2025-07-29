"""
Pydantic models for validating the mcp_servers.json configuration file.
"""
from pydantic import BaseModel, validator, HttpUrl, FilePath, DirectoryPath, Field, root_validator
from typing import Dict, Union, Optional, Literal, Any

class MCPBaseAuthConfig(BaseModel):
    """Base model for authentication configurations."""
    type: str
    auth_source: Literal["env", "file"] = Field("env", description="Source of the auth credential ('env' or 'file').")

class MCPBasicAuthConfig(MCPBaseAuthConfig):
    type: Literal["basic"] = "basic"
    username_env_var: Optional[str] = Field(default=None, description="Environment variable for basic auth username (if auth_source is 'env').")
    password_env_var: Optional[str] = Field(default=None, description="Environment variable for basic auth password (if auth_source is 'env').")
    username_file_path: Optional[FilePath] = Field(default=None, description="Path to file containing username (if auth_source is 'file').")
    password_file_path: Optional[FilePath] = Field(default=None, description="Path to file containing password (if auth_source is 'file').")

    @root_validator(skip_on_failure=True)
    def check_basic_auth_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        auth_source = values.get("auth_source")
        if auth_source == "env":
            if not values.get("username_env_var") or not values.get("password_env_var"):
                raise ValueError("If auth_source is 'env' for basic auth, 'username_env_var' and 'password_env_var' must be set.")
        elif auth_source == "file":
            if not values.get("username_file_path") or not values.get("password_file_path"):
                raise ValueError("If auth_source is 'file' for basic auth, 'username_file_path' and 'password_file_path' must be set.")
        return values

class MCPBearerAuthConfig(MCPBaseAuthConfig):
    type: Literal["bearer"] = "bearer"
    token_env_var: Optional[str] = Field(default=None, description="Environment variable for the bearer token (if auth_source is 'env').")
    token_file_path: Optional[FilePath] = Field(default=None, description="Path to file containing the bearer token (if auth_source is 'file').")

    @root_validator(skip_on_failure=True)
    def check_bearer_auth_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        auth_source = values.get("auth_source")
        if auth_source == "env" and not values.get("token_env_var"):
            raise ValueError("If auth_source is 'env' for bearer auth, 'token_env_var' must be set.")
        if auth_source == "file" and not values.get("token_file_path"):
            raise ValueError("If auth_source is 'file' for bearer auth, 'token_file_path' must be set.")
        return values

class MCPAPIKeyAuthConfig(MCPBaseAuthConfig):
    type: Literal["api_key"] = "api_key"
    token_env_var: Optional[str] = Field(default=None, description="Environment variable for the API key (if auth_source is 'env').")
    token_file_path: Optional[FilePath] = Field(default=None, description="Path to file containing the API key (if auth_source is 'file').")
    key_name: str = Field("X-API-Key", description="Header or query parameter name for the API key.")
    location: Literal["header", "query"] = Field("header", description="Location of API key: 'header' or 'query'.")

    @root_validator(skip_on_failure=True)
    def check_apikey_auth_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        auth_source = values.get("auth_source")
        if auth_source == "env" and not values.get("token_env_var"):
            raise ValueError("If auth_source is 'env' for api_key auth, 'token_env_var' must be set.")
        if auth_source == "file" and not values.get("token_file_path"):
            raise ValueError("If auth_source is 'file' for api_key auth, 'token_file_path' must be set.")
        return values

AnyMCPAuthConfig = Union[MCPBasicAuthConfig, MCPBearerAuthConfig, MCPAPIKeyAuthConfig]

class MCPServerBaseConfig(BaseModel):
    type: str 
    authentication: Optional[AnyMCPAuthConfig] = Field(default=None, description="Authentication configuration for the server.", discriminator='type')

class MCPServerConfigLocal(MCPServerBaseConfig):
    type: Literal["local"] = "local"
    project_path: DirectoryPath = Field(..., description="Path to the local MCP server project directory.")
    run_command: str = Field(..., description="Command to run the local MCP server.")
    port: int = Field(..., gt=0, lt=65536, description="Port number the local server will listen on.")
    env_file_path: Optional[FilePath] = Field(default=None, description="Optional path to the .env file for the local server.")
    healthcheck_path: Optional[str] = Field(default=None, description="Optional healthcheck path (e.g., '/health').")
    auto_start: bool = Field(False, description="Attempt to auto-start this local server when client is requested.")
    dockerfile_path: Optional[str] = Field(default=None, description="Relative path to the Dockerfile within the project_path.")
    docker_image_name: Optional[str] = Field(default=None, description="Custom Docker image name to build or use.")
    compose_service_name: Optional[str] = Field(default=None, description="Service name for Docker Compose integration (defaults to server_name).")
    compose_managed: bool = Field(False, description="If true, SDK may attempt to integrate/manage this with a project's docker-compose.yml.")
    project_compose_file_path: Optional[str] = Field(default=None, description="Path to the main project's docker-compose.yml that includes this service.")

class MCPServerConfigRemote(MCPServerBaseConfig):
    type: Literal["remote"] = "remote"
    url: HttpUrl = Field(..., description="URL of the remote MCP server.")

AnyMCPServerConfig = Union[MCPServerConfigLocal, MCPServerConfigRemote]

class MCPConfigurationFile(BaseModel):
    version: str = Field("1.0", description="Schema version of the configuration file.")
    mcp_servers: Dict[str, AnyMCPServerConfig] = Field(default_factory=dict, description="Dictionary of configured MCP servers.")

    @validator("version")
    def version_must_be_supported(cls, v: str) -> str:
        if v != "1.0":
            raise ValueError(f"Unsupported configuration version '{v}'. Only '1.0' is currently supported.")
        return v
