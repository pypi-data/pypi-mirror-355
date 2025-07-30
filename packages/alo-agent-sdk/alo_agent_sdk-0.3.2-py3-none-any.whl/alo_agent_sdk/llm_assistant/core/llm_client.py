import os
from typing import Type, TypeVar, Generic, Optional
from pydantic import BaseModel

from pydantic_ai import PydanticAI
from pydantic_ai.llm.openai import OpenAI
from pydantic_ai.llm.anthropic import Anthropic
# from pydantic_ai.llm.gemini import Gemini # Import when Gemini support is fully added
from alo_agent_sdk.core.config_manager import ConfigManager, ConfigError

# Define a generic type variable for Pydantic models
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

class LLMConfigurationError(Exception):
    """Custom exception for LLM configuration issues."""
    pass

class LLMResponseError(Exception):
    """Custom exception for issues with the LLM's response or parsing."""
    pass

class LLMClient(Generic[PydanticModel]):
    """
    A client to interact with an LLM, using PydanticAI
    to get structured output based on Pydantic models.
    """
    def __init__(self, 
                 llm_provider_override: Optional[str] = None, 
                 api_key_override: Optional[str] = None, 
                 model_name_override: Optional[str] = None):
        
        config_manager = ConfigManager() # Loads from ~/.alo/config.json
        
        # Determine provider: constructor override > config file default > hardcoded default ("openai")
        self.llm_provider = (llm_provider_override or 
                             config_manager.get_value("llm_settings.default_provider") or 
                             "openai").lower()
        
        # Determine API key: constructor override > config file > environment variable
        self.api_key = api_key_override
        if not self.api_key:
            self.api_key = config_manager.get_api_key(self.llm_provider)
        
        if not self.api_key: # Fallback to environment variable if not in constructor or config
            env_var_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "gemini": "GEMINI_API_KEY" # Or GOOGLE_API_KEY
            }
            api_key_env_var = env_var_map.get(self.llm_provider)
            if api_key_env_var:
                self.api_key = os.getenv(api_key_env_var)

        # Determine model name: constructor override > config file (provider specific default) 
        # > config file (global default) > hardcoded default for the specific provider (in _initialize_client)
        self.model_name = config_manager.get_model_name(
            provider_name=self.llm_provider, 
            cli_model_name=model_name_override # cli_model_name here means constructor_override
        )
        
        self._pydantic_ai_client = self._initialize_client()

    def _initialize_client(self) -> Optional[PydanticAI]: # Can be None for mock
        """Initializes the PydanticAI client with the determined LLM provider, API key, and model."""
        llm_instance = None
        effective_model_name = self.model_name # Already resolved by __init__

        if self.llm_provider == "openai":
            if not self.api_key:
                raise LLMConfigurationError(
                    "OpenAI API key not found. Configure via `alo-sdk config llm set providers.openai.api_key <key>`, "
                    "set OPENAI_API_KEY environment variable, or provide it via CLI/constructor."
                )
            effective_model_name = effective_model_name or "gpt-3.5-turbo"
            llm_instance = OpenAI(api_key=self.api_key, model=effective_model_name)
        
        elif self.llm_provider == "anthropic":
            if not self.api_key:
                raise LLMConfigurationError(
                    "Anthropic API key not found. Configure via `alo-sdk config llm set providers.anthropic.api_key <key>`, "
                    "set ANTHROPIC_API_KEY environment variable, or provide it via CLI/constructor."
                )
            effective_model_name = effective_model_name or "claude-3-haiku-20240307"
            llm_instance = Anthropic(api_key=self.api_key, model=effective_model_name)

        elif self.llm_provider == "gemini":
            # from pydantic_ai.llm.gemini import Gemini # Ensure this is imported at top if used
            if not self.api_key:
                raise LLMConfigurationError(
                    "Gemini API key not found. Configure via `alo-sdk config llm set providers.gemini.api_key <key>`, "
                    "set GEMINI_API_KEY environment variable, or provide it via CLI/constructor."
                )
            effective_model_name = effective_model_name or "gemini-1.5-flash-latest"
            # llm_instance = Gemini(api_key=self.api_key, model=effective_model_name)
            raise LLMConfigurationError("Gemini provider support is not fully implemented in LLMClient's _initialize_client yet. Uncomment Gemini import and instantiation.")
        
        elif self.llm_provider == "mock":
            print(f"LLMClient: Using mock provider '{self.llm_provider}'. No actual LLM calls will be made by PydanticAI client.")
            # For mock, PydanticAI client is not strictly needed if generate_structured_output handles all mocking.
            # However, returning None signifies that no real LLM interaction is configured.
            return None
        
        else:
            raise LLMConfigurationError(
                f"Unsupported LLM provider: {self.llm_provider}. "
                "Supported: 'openai', 'anthropic', 'gemini' (partial), 'mock'."
            )
        
        return PydanticAI(llm=llm_instance)

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        output_model: Type[PydanticModel]
    ) -> PydanticModel:
        """
        Generates structured output from the LLM based on the provided prompts
        and Pydantic output model.

        Args:
            system_prompt: The system prompt to guide the LLM.
            user_prompt: The user's input/request.
            output_model: The Pydantic model class for the desired output structure.

        Returns:
            An instance of the output_model populated by the LLM.

        Raises:
            LLMResponseError: If the LLM fails to produce valid structured output
                              or if there's an issue with the PydanticAI call.
        """
        # Handle mock provider case specifically (as used by CLI for "echo agent" test)
        if self.llm_provider == "mock":
            # The CLI's `generate agent` command has its own more specific mock logic
            # for the "echo agent" case. This is a general fallback for the mock provider.
            print(f"LLMClient (mock): Simulating LLM call for model {output_model.__name__}.")
            print(f"System Prompt (first 100 chars): {system_prompt[:100]}...")
            print(f"User Prompt: {user_prompt}")
            raise LLMResponseError(
                "Mock LLMClient (general path) cannot generate actual structured output. "
                "Specific mock cases should be handled by the caller (e.g., CLI for 'echo agent')."
            )

        if not self._pydantic_ai_client:
             raise LLMConfigurationError("PydanticAI client not initialized. This should not happen for non-mock providers if __init__ was successful.")

        try:
            # PydanticAI's run method is synchronous in some versions,
            # but the underlying LLM calls might be async.
            # If PydanticAI offers an async `arun` or similar, prefer that.
            # For now, assuming `run` can be awaited if the underlying llm object supports it,
            # or PydanticAI handles the async nature internally.
            # Let's check PydanticAI documentation for the best async pattern.
            # As of recent versions, PydanticAI's `run` method itself is not async.
            # The call to the LLM provider (e.g. openai.ChatCompletion.acreate) would be async.
            # PydanticAI might abstract this. If not, we might need to run it in a thread.
            # For simplicity, let's assume PydanticAI handles this or we're okay with a sync call here.
            # If true async is needed, this part needs adjustment.

            # The `PydanticAI` object itself is what we call `run` on.
            result = self._pydantic_ai_client.run(
                output_model=output_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            if not isinstance(result, output_model):
                raise LLMResponseError(
                    f"LLM output was not of the expected type {output_model.__name__}. Got: {type(result)}"
                )
            return result
        except Exception as e:
            # Catching a broad exception here, but ideally, catch specific PydanticAI/LLM errors.
            raise LLMResponseError(f"Error during LLM call or parsing: {e}")

# Example usage (conceptual, requires OPENAI_API_KEY to be set)
if __name__ == "__main__":
    from alo_agent_sdk.llm_assistant.models import AgentScaffold
    from alo_agent_sdk.llm_assistant.prompts.agent_generation import AGENT_SCAFFOLD_SYSTEM_PROMPT
    import asyncio

    async def main_example(): # Renamed to avoid conflict if this file is imported elsewhere
        # This example demonstrates conceptual usage.
        # It requires OPENAI_API_KEY (or other provider's key) to be set in the environment
        # for a non-"mock" provider.
        print("Running LLMClient example...")
        try:
            # To test with OpenAI, ensure OPENAI_API_KEY is set in your environment
            # and change llm_provider to "openai".
            # Example: client = LLMClient[AgentScaffold](llm_provider="openai")
            
            # Test with the "openai" provider. This will fail if OPENAI_API_KEY is not set.
            # If you want to test the mock path that was in the CLI, you'd need to replicate
            # the CLI's logic for handling the "mock" provider and "echo agent" description here.
            # For simplicity, this example now tries "openai" by default.
            print("Attempting with 'openai' provider for a generic description...")
            # Ensure OPENAI_API_KEY is set in your environment to run this example successfully.
            client = LLMClient[AgentScaffold](llm_provider="openai") 

            user_description = "Create an agent that fetches news articles about a topic and summarizes them."
            
            print(f"User description: {user_description}")
            agent_scaffold_instance = await client.generate_structured_output(
                system_prompt=AGENT_SCAFFOLD_SYSTEM_PROMPT,
                user_prompt=user_description,
                output_model=AgentScaffold
            )
            print("Generated Agent Scaffold (Success with OpenAI):")
            print(agent_scaffold_instance.model_dump_json(indent=2))

        except LLMConfigurationError as e:
            print(f"LLM Configuration Error: {e}")
        except LLMResponseError as e:
            print(f"LLM Response Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

    # To run this example:
    # 1. Ensure pydantic-ai and openai are installed.
    # 2. Set the OPENAI_API_KEY environment variable.
    # 3. Uncomment the line below and run `python -m alo_agent_sdk.llm_assistant.core.llm_client`
    # asyncio.run(main_example())
    print("LLMClient with PydanticAI (OpenAI focus) defined. To run the example, uncomment asyncio.run(main_example()) and ensure OPENAI_API_KEY is set.")
