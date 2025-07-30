from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ToolParameter(BaseModel):
    name: str = Field(..., description="Name of the parameter for the tool function.")
    type_hint: str = Field(..., description="Python type hint for the parameter (e.g., 'str', 'int', 'bool').")
    description: Optional[str] = Field(None, description="Optional description of the parameter.")

class ToolDefinition(BaseModel):
    tool_name: str = Field(..., description="The name of the Python function for the tool (e.g., 'translate_text').")
    description: str = Field(..., description="The description of the tool that will be used in the @agent.tool() decorator and for MCP documentation.")
    code_stub: str = Field(..., description="The Python code snippet for the async tool function, including type hints, parameters, and a basic docstring. It should be a complete, runnable function body.")
    parameters: List[ToolParameter] = Field(default_factory=list, description="A list of parameters the tool function will accept.")
    return_type: str = Field(default="str", description="The Python type hint for the return value of the tool function (e.g., 'str', 'dict', 'List[str]').")

class AgentScaffold(BaseModel):
    agent_name: str = Field(..., description="The name of the agent (e.g., 'TranslationAgent', 'EchoAgentLLM').")
    version: str = Field(default="0.1.0", description="The version of the agent.")
    description: str = Field(..., description="A brief description of what the agent does.")
    registry_url_env_var: str = Field(default="ALO_REGISTRY_URL", description="The environment variable name for the Agent Registry URL.")
    registry_url_default: str = Field(default="http://localhost:8001", description="The default Agent Registry URL if the environment variable is not set.")
    tools: List[ToolDefinition] = Field(default_factory=list, description="A list of tools the agent will provide.")
    additional_dependencies: List[str] = Field(default_factory=list, description="List of additional Python packages required by the agent, to be included in requirements.txt (e.g., 'requests', 'beautifulsoup4').")
    dockerfile_template_path: str = Field(default="alo_agent_sdk/templates/docker/Dockerfile.agent.template", description="Path to the Dockerfile template to use.")
    requirements_sdk_path: str = Field(default="alo_agent_sdk/templates/docker/requirements.sdk.txt", description="Path to the base SDK requirements file.")
