# alo-agent-sdk

SDK for building and deploying AI agents.

## Overview

This SDK provides tools and utilities to:
- Standardize the creation of AI agents as FastAPI services.
- Define agent capabilities using the Model Context Protocol (MCP) via `python_a2a`.
- Containerize agents using Docker.
- Deploy agents and an Agent Registry Service to Google Cloud Run.

## Features

- **AgentBuilder**: Simplifies the creation of `python_a2a` compatible agents.
- **RegistryClient**: For agent interaction with the Agent Registry Service.
- **AgentRegistryService**: A FastAPI-based implementation of an agent registry.
- **Deployment Scripts**: Utilities for deploying to Google Cloud Run.
- **Templates**: Dockerfile templates for agents and the registry service.

## Getting Started

This guide will walk you through installing the ALO Agent SDK, creating a simple agent, and deploying it.

### Prerequisites

*   Python 3.8+
*   Docker installed locally (for building container images)
*   Google Cloud SDK (`gcloud` CLI) installed and configured (for Cloud Run deployment)
    *   Ensure you have authenticated with `gcloud auth login` and `gcloud auth application-default login`.
    *   Set your default project with `gcloud config set project YOUR_PROJECT_ID`.
    *   Enable the Cloud Run API, Artifact Registry API, and Cloud Build API in your GCP project.

### 1. Installation

Currently, the SDK is under development. To use it, you would typically clone the repository and install it in editable mode:

```bash
git clone https://github.com/yourusername/alo_agent_sdk.git # Replace with actual repo URL
cd alo_agent_sdk
pip install -e .
```
*(Once published, it would be `pip install alo-agent-sdk`)*

### 2. Create your First Agent

Let's create a simple "Echo Agent" that echoes back any message it receives.

1.  **Create a project directory for your agent:**
    ```bash
    mkdir my_echo_agent
    cd my_echo_agent
    ```

2.  **Create your main agent file (e.g., `main.py`):**
    ```python
    # my_echo_agent/main.py
    from alo_agent_sdk.core import AgentBuilder
    import os

    # Configure the agent
    # For Cloud Run, ALO_AGENT_BASE_URL will be derived from the service URL.
    # ALO_REGISTRY_URL should be set as an environment variable in Cloud Run.
    agent = AgentBuilder(
        name="EchoAgent",
        version="0.1.0",
        description="A simple agent that echoes messages.",
        registry_url=os.getenv("ALO_REGISTRY_URL", "http://localhost:8001") # Default for local
    )

    @agent.tool(description="Echoes back the input message.")
    async def echo(message: str) -> str:
        """
        Receives a message and returns it prefixed with 'Echo: '.
        """
        print(f"Echoing message: {message}")
        return f"Echo: {message}"

    # Get the FastAPI app instance from the builder
    app = agent.get_fastapi_app()

    # For local execution (optional, Uvicorn is usually run by Docker CMD)
    if __name__ == "__main__":
        import uvicorn
        port = int(os.getenv("PORT", 8080))
        print(f"Starting EchoAgent locally on http://localhost:{port}")
        # Note: For local testing with registration, ensure the registry service is running.
        # The agent_base_url for local registration might need to be explicitly set
        # if not using the default http://localhost:PORT.
        # e.g., agent = AgentBuilder(..., agent_base_url="http://your-local-ip:8080")
        uvicorn.run(app, host="0.0.0.0", port=port)
    ```

3.  **Create a `requirements.txt` for any specific dependencies (optional):**
    For this simple agent, it might be empty if it only relies on the SDK.
    ```
    # my_echo_agent/requirements.txt
    # Add any specific dependencies for your agent here
    ```

4.  **Prepare your `Dockerfile`:**
    *   Copy `alo_agent_sdk/templates/docker/requirements.sdk.txt` to your agent's project directory (`my_echo_agent/requirements.sdk.txt`).
    *   Copy `alo_agent_sdk/templates/docker/Dockerfile.agent.template` to `my_echo_agent/Dockerfile`.
    *   Ensure the `CMD` in your `Dockerfile` correctly points to your FastAPI app instance (e.g., `main:app` if your file is `main.py` and instance is `app`).

### 3. Deploy the Agent Registry Service (One-time setup or if not already running)

The agents need a registry service to register with and for discovery.

1.  **Navigate to the SDK's example for registry deployment:**
    (Assuming you have the `alo_agent_sdk` cloned)
    ```bash
    cd path/to/alo_agent_sdk/examples/example_registry_deploy
    ```
    *   This directory contains a `Dockerfile` based on `Dockerfile.registry.template`.
    *   It also needs `requirements.sdk.txt` (copy it from `alo_agent_sdk/templates/docker/`).
    *   It also needs the `alo_agent_sdk` source code to be in the Docker build context (as per `COPY alo_agent_sdk ./alo_agent_sdk` in its Dockerfile). A simple way is to run the deploy script from the root of the `alo_agent_sdk` checkout, adjusting paths.

2.  **Deploy using the `deploy_cloud_run.sh` script:**
    (Assuming you are in the root of the `alo_agent_sdk` cloned repository)
    ```bash
    ./scripts/gcp/cloud_run/deploy_cloud_run.sh \
      -s alo-registry-service \
      -p YOUR_GCP_PROJECT_ID \
      -c examples/example_registry_deploy # Source path for build context
      # The Dockerfile used will be examples/example_registry_deploy/Dockerfile
    ```
    Take note of the URL of the deployed registry service. You'll need to set this as `ALO_REGISTRY_URL` for your agents.

### 4. Deploy your Echo Agent to Cloud Run

1.  **Navigate to your agent's project directory:**
    ```bash
    cd path/to/my_echo_agent
    ```

2.  **Run the deployment script:**
    (Assuming `deploy_cloud_run.sh` is in your PATH or you provide the full path to it)
    ```bash
    # Path to deploy_cloud_run.sh from alo_agent_sdk
    DEPLOY_SCRIPT_PATH="../path/to/alo_agent_sdk/scripts/gcp/cloud_run/deploy_cloud_run.sh" 
    
    # Ensure your GCP Project ID is set
    GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"
    # URL of your deployed Agent Registry Service
    REGISTRY_SERVICE_URL="YOUR_REGISTRY_SERVICE_URL" 

    bash $DEPLOY_SCRIPT_PATH \
      -s echo-agent \
      -p $GCP_PROJECT_ID \
      -e "ALO_REGISTRY_URL=$REGISTRY_SERVICE_URL" 
      # -c . (source path defaults to current directory)
      # The script expects 'Dockerfile' in the current directory.
    ```
    This will build your agent's Docker image, push it to Google Artifact Registry, and deploy it to Cloud Run. The `ALO_REGISTRY_URL` environment variable tells your agent where to find the registry. The agent will also try to determine its own public URL (e.g., from `ALO_AGENT_SERVICE_URL` which can be set based on Cloud Run's `K_SERVICE` URL or similar).

### 5. Test your Agent

Once deployed, you can find your agent's URL in the Cloud Run console or from the output of the deploy script.

*   **Agent Card:** Access `https://your-echo-agent-url.a.run.app/agent.json`
*   **MCP Tool:** You can call the `echo` tool via a POST request to `https://your-echo-agent-url.a.run.app/tools/echo` with a JSON body like:
    ```json
    {
      "message": "Hello from ALO SDK!"
    }
    ```

### Next Steps

*   Explore the `alo_agent_sdk.core.AgentBuilder` to add more complex tools and resources.
*   Check the `examples/` directory in the SDK for more usage patterns.
*   Implement more sophisticated agents!

## Managing External MCP Servers

The ALO Agent SDK provides a comprehensive suite of tools for configuring, managing, and interacting with external Model Context Protocol (MCP) servers. This allows your agents to seamlessly leverage tools and resources from other services.

### Overview

Configurations for MCP servers are managed via the SDK's command-line interface (CLI) and stored in an `mcp_servers.json` file located in the `.alo_project` subdirectory of your project root. The `MCPManager` class in your agent code then uses this configuration to provide `MCPClient` instances.

Key capabilities include:
*   Interactive CLI for easy configuration.
*   Support for local (process-based or Docker-managed) and remote MCP servers.
*   Lifecycle management for local servers (start, stop, status, auto-start).
*   Flexible authentication methods, including sourcing credentials from environment variables or files.
*   Automatic reloading of configurations if `mcp_servers.json` is modified.
*   Pydantic-based validation of the `mcp_servers.json` schema.

### Configuration File (`.alo_project/mcp_servers.json`)

This JSON file is automatically created and managed by the `alo-sdk mcp` commands. It stores an object where each key is a server name, and the value is its configuration.

### CLI Commands

All MCP-related commands are under the `alo-sdk mcp` subcommand.

*   **`alo-sdk mcp configure <server_name> --type <TYPE> [options...]`**
    *   Adds or updates an MCP server configuration. This command is **interactive**: if key information is not provided via options, the CLI will prompt for it.
    *   **Common Options:**
        *   `--type <remote|local>`: (Mandatory) Server type.
        *   `--auth-type <none|basic|bearer|api_key>`: Authentication method.
        *   `--auth-source <env|file>`: Where to load credentials from (default: `env`).
        *   See "Authentication Methods" below for more auth options.
    *   **For `--type remote`:**
        *   `--url <URL>`: (Mandatory) The URL of the remote MCP server.
    *   **For `--type local`:**
        *   `--project-path <PATH>`: (Mandatory) Path to the local server's project directory.
        *   `--run-command "<COMMAND>"`: (Mandatory) Command to start the server if not using Docker Compose.
        *   `--port <PORT>`: (Mandatory) Port the local server listens on.
        *   `--env-file <PATH>`: Optional path to a `.env` file for the local server.
        *   `--healthcheck-path <PATH>`: Optional HTTP path for health checks.
        *   `--auto-start / --no-auto-start`: Enable/disable auto-starting this server.
        *   **Docker Options for Local Servers:**
            *   `--dockerfile <PATH>`: Relative path to Dockerfile within `project-path`.
            *   `--docker-image <NAME>`: Custom Docker image name.
            *   `--compose-service-name <NAME>`: Service name in Docker Compose (defaults to `server_name`).
            *   `--compose-managed / --no-compose-managed`: If SDK should manage this service via `docker-compose` commands.
            *   `--project-compose-file <PATH>`: Path to the main `docker-compose.yml` if `compose-managed` is true.
            *   `--compose-generate-snippet`: If set, prints a suggested YAML snippet for `docker-compose.yml`.

*   **`alo-sdk mcp list`**
    *   Lists all configured MCP servers.

*   **`alo-sdk mcp describe <server_name>`**
    *   Shows the detailed configuration for a specific server.

*   **`alo-sdk mcp remove <server_name>`**
    *   Removes a server's configuration.

*   **`alo-sdk mcp start <server_name>`**
    *   Manually starts a configured local MCP server (either as a direct process or via `docker-compose` if `compose_managed`).

*   **`alo-sdk mcp stop <server_name>`**
    *   Manually stops a running local MCP server managed by the SDK.

*   **`alo-sdk mcp status [<server_name>]`**
    *   Shows the running status of one or all configured local MCP servers.

### Authentication Methods

When configuring authentication (`--auth-type ...`), you can specify the source of credentials using `--auth-source <env|file>` (defaults to `env`).

*   **`env` (Environment Variables):**
    *   `--auth-username-env <VAR_NAME>`: For basic auth username.
    *   `--auth-password-env <VAR_NAME>`: For basic auth password.
    *   `--auth-token-env <VAR_NAME>`: For bearer tokens or API keys.
    *   The SDK will read the actual secret from the specified environment variable at runtime.
*   **`file` (File Paths):**
    *   `--auth-username-file <FILE_PATH>`: For basic auth username.
    *   `--auth-password-file <FILE_PATH>`: For basic auth password.
    *   `--auth-token-file <FILE_PATH>`: For bearer tokens or API keys.
    *   The SDK will read the actual secret from the content of the specified file at runtime. This is useful for secrets mounted into containers.
*   **API Key Specifics:**
    *   `--auth-apikey-name <HEADER_NAME>`: Name of the header or query parameter (default: `X-API-Key`).
    *   `--auth-apikey-location <header|query>`: Where the API key is sent (default: `header`).

### Using `MCPManager` in Your Agent

The `MCPManager` class is the primary way your agent code interacts with configured MCP servers.

**Key Features of `MCPManager`:**
*   **Automatic Configuration Loading:** Reads `mcp_servers.json` from your project's `.alo_project` directory (or an explicitly provided path). It uses Pydantic for schema validation.
*   **Intelligent Caching & Reloading:** Caches `MCPClient` instances. It monitors `mcp_servers.json` for changes; if the file is modified, the manager automatically reloads the configuration (and attempts to stop/restart relevant services if auto-managed) before providing a client.
*   **Lifecycle Management for Local Servers:**
    *   **Auto-Start:** If a local server has `auto_start: true`, `MCPManager` attempts to start it (as a direct process or via `docker-compose` if `compose_managed: true`) when `get_client()` is called. Health checks are performed if configured.
    *   **Graceful Shutdown:** `await manager.close_all_clients()` closes client connections and attempts to stop all local servers started by that manager instance.
*   **Flexible Credential Handling:** Retrieves secrets from environment variables or files based on the `auth_source` in the configuration.

**Example Usage:**
```python
# In your agent's code (e.g., main.py or a specific module)
from alo_agent_sdk.alo_a2a.mcp.manager import MCPManager, MCPConfigError, MCPAuthEnvError
from alo_agent_sdk.alo_a2a.mcp.client import MCPClientError # For client communication errors
import asyncio
import os

# Ensure required environment variables for auth are set (e.g., WEATHER_API_KEY_ENV_VAR from the example above)
# os.environ["WEATHER_API_KEY_ENV_VAR"] = "your_actual_api_key_if_testing_locally"

async def interact_with_mcp_servers():
    manager = MCPManager() # Assumes mcp_servers.json is in the project root (current working directory)
                           # Or pass config_path=Path("path/to/mcp_servers.json")

    # Example: Get a client for the 'external-weather-service' configured earlier
    server_name_to_use = "external-weather-service" # Or "my-local-js-mcp"

    if server_name_to_use not in manager.list_server_names():
        print(f"Server '{server_name_to_use}' is not configured. Please use 'alo-sdk mcp configure ...'")
        return

    try:
        print(f"Attempting to get client for '{server_name_to_use}'...")
        weather_client = await manager.get_client(server_name_to_use)
        
        print(f"Fetching tools from '{server_name_to_use}'...")
        tools = await weather_client.get_tools()
        tool_names = [tool.get('name', 'N/A') for tool in tools]
        print(f"Available tools: {tool_names}")

        # Example: If 'get_forecast' tool exists (replace with actual tool and params)
        # if "get_forecast" in tool_names:
        #     forecast = await weather_client.call_tool("get_forecast", city="London")
        #     print(f"Forecast for London: {forecast}")

    except MCPConfigError as e:
        print(f"MCP Configuration Error: {e}")
    except MCPAuthEnvError as e:
        print(f"MCP Authentication Environment Variable Error: {e}")
    except MCPClientError as e: # Covers connection, timeout, tool execution errors from client
        print(f"MCP Client Error for '{server_name_to_use}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing all MCP clients...")
        await manager.close_all_clients()

if __name__ == "__main__": # Example of running the interaction
    # This block would typically be part of your agent's startup or a specific task.
    # For a local server, ensure it's running before this script is executed.
    # asyncio.run(interact_with_mcp_servers())
    pass
```

This system allows for a clean separation between configuring external service connections and using them within your agent's logic. Remember to set any required environment variables for authentication before your agent runs.

## Project Structure

```
alo_agent_sdk/
├── core/
│   ├── agent_builder.py
│   └── registry_client.py
├── registry_service/
│   ├── main.py
│   └── models.py
├── templates/
│   └── docker/
│       ├── Dockerfile.agent.template
│       ├── Dockerfile.registry.template
│       └── requirements.sdk.txt
├── scripts/
│   └── gcp/
│       └── cloud_run/
│           └── deploy_cloud_run.sh
├── examples/
│   ├── example_agent/
│   └── example_registry_deploy/
├── docs/
├── pyproject.toml
└── README.md
```

## Contributing

*(Contribution guidelines to be added)*

## License

*(License information to be added, e.g., MIT License)*
