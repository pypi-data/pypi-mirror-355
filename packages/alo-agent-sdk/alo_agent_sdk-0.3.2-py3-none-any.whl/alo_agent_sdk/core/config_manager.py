import json
from pathlib import Path
from typing import Any, Optional, Dict, Union, List

from pydantic import ValidationError

from alo_agent_sdk.core.config_models import SDKConfig, LLMSettings, LLMProviderSettings, OpenAIConfig, AnthropicConfig, GeminiConfig

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass

class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path: Path = config_path or SDKConfig.get_active_config_path()
        self.config: SDKConfig = self._load_config()

    def _load_config(self) -> SDKConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return SDKConfig(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                # Consider backing up the corrupted file and starting fresh
                # For now, we'll raise an error or return a default config
                print(f"Warning: Error loading config file {self.config_path}: {e}. Using default configuration.")
                return SDKConfig() # Return default config if loading fails
            except Exception as e:
                print(f"Warning: Unexpected error loading config file {self.config_path}: {e}. Using default configuration.")
                return SDKConfig()
        return SDKConfig()

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config.model_dump(mode="json"), f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration to {self.config_path}: {e}")

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a value from the configuration using a dot-separated key path.
        Example: "llm_settings.default_provider"
        """
        keys = key_path.split('.')
        current_level: Union[Dict[str, Any], BaseModel] = self.config.model_dump() # Start with the whole config dict
        
        for key in keys:
            if isinstance(current_level, dict):
                if key in current_level:
                    current_level = current_level[key]
                else:
                    return default
            elif isinstance(current_level, BaseModel): # Should not happen if we start with dict
                 if hasattr(current_level, key):
                    current_level = getattr(current_level, key)
                 else:
                    return default
            else: # Reached a non-dict, non-BaseModel value before end of path
                return default
        return current_level

    def set_value(self, key_path: str, value: Any):
        """
        Sets a value in the configuration using a dot-separated key path.
        Example: "llm_settings.providers.openai.api_key"
        This is a bit complex due to nested Pydantic models.
        We'll update the self.config object and then re-validate and save.
        """
        keys = key_path.split('.')
        
        # To update nested Pydantic models correctly, it's often easier to
        # load the current config into a dict, update the dict, then parse back into SDKConfig.
        # This ensures Pydantic's validation and model structure are respected.

        config_dict = self.config.model_dump(mode="json")
        current_level_dict = config_dict
        
        for i, key in enumerate(keys[:-1]): # Iterate up to the second to last key
            if key not in current_level_dict or not isinstance(current_level_dict[key], dict):
                current_level_dict[key] = {} # Create intermediate dicts if they don't exist
            current_level_dict = current_level_dict[key]
        
        last_key = keys[-1]
        current_level_dict[last_key] = value
        
        try:
            # Re-validate the entire structure by creating a new SDKConfig instance
            self.config = SDKConfig(**config_dict)
            self._save_config()
        except ValidationError as e:
            raise ConfigError(f"Failed to set value for '{key_path}' due to validation error: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to set value for '{key_path}': {e}")

    def remove_value(self, key_path: str):
        """
        Removes a value from the configuration using a dot-separated key path.
        Setting a value to None might be preferable for Pydantic models to reset to defaults.
        True removal from dict might make the model invalid if the field is required.
        This implementation will attempt to set the value to None.
        """
        # For Pydantic models, "removing" often means setting to None or default.
        # A more robust approach might involve rebuilding the model or using model-specific unset methods.
        # For now, let's try setting to None if possible, or handle specific cases.
        
        # This is a simplified approach. True "removal" that Pydantic handles gracefully
        # often means creating a new model instance without that field, or relying on `exclude_unset`.
        # For nested structures, this is complex.
        # A common pattern is to set to None and let Pydantic handle defaults on next load/dump if `exclude_none=True` is used.

        keys = key_path.split('.')
        config_dict = self.config.model_dump(mode="json")
        current_level_dict = config_dict
        
        for i, key in enumerate(keys[:-1]):
            if key not in current_level_dict or not isinstance(current_level_dict[key], dict):
                # Path doesn't exist, so nothing to remove
                print(f"Warning: Path '{key_path}' not found for removal.")
                return 
            current_level_dict = current_level_dict[key]
        
        last_key = keys[-1]
        if last_key in current_level_dict:
            del current_level_dict[last_key] # Try to delete the key
            try:
                self.config = SDKConfig(**config_dict) # Re-validate
                self._save_config()
            except ValidationError as e:
                # If deletion causes validation error (e.g. required field), revert or handle
                print(f"Warning: Could not directly remove '{key_path}' due to validation. Consider setting to default or None. Error: {e}")
                # As a fallback, try setting to None if it's an optional field,
                # but this requires more introspection of the model.
                # For now, we'll just log the warning. A more sophisticated `remove` would be needed.
            except Exception as e:
                 raise ConfigError(f"Failed to update config after attempting to remove '{key_path}': {e}")
        else:
            print(f"Warning: Key '{last_key}' not found at path for removal.")


    # Convenience methods for LLM settings
    def get_llm_settings(self) -> LLMSettings:
        return self.config.llm_settings

    def get_llm_provider_config(self, provider_name: str) -> Optional[Union[OpenAIConfig, AnthropicConfig, GeminiConfig]]:
        if provider_name == "openai":
            return self.config.llm_settings.providers.openai
        elif provider_name == "anthropic":
            return self.config.llm_settings.providers.anthropic
        elif provider_name == "gemini":
            return self.config.llm_settings.providers.gemini
        return None

    def get_api_key(self, provider_name: str) -> Optional[str]:
        provider_conf = self.get_llm_provider_config(provider_name)
        return provider_conf.api_key if provider_conf else None

    def get_model_name(self, provider_name: str, cli_model_name: Optional[str] = None) -> Optional[str]:
        """Gets model name: CLI override > provider default > global default (less common)."""
        if cli_model_name:
            return cli_model_name
        
        provider_conf = self.get_llm_provider_config(provider_name)
        if provider_conf and provider_conf.default_model:
            return provider_conf.default_model
        
        # Fallback to global default_model_name if provider specific is not set
        if self.config.llm_settings.default_model_name:
            return self.config.llm_settings.default_model_name
            
        # Fallback for OpenAI if no other default is found (as per original LLMClient)
        if provider_name == "openai":
            return "gpt-3.5-turbo" 
        return None


if __name__ == "__main__":
    # Example Usage
    manager = ConfigManager()
    print(f"Config file used: {manager.config_path}")
    
    # Show current config
    print("\nCurrent LLM Settings:")
    print(json.dumps(manager.get_llm_settings().model_dump(mode="json"), indent=2))

    # Example: Set OpenAI API Key and default model
    print("\nSetting OpenAI API key and model...")
    try:
        manager.set_value("llm_settings.providers.openai.api_key", "sk-testkey123")
        manager.set_value("llm_settings.providers.openai.default_model", "gpt-4o")
        manager.set_value("llm_settings.default_provider", "openai")
        print("OpenAI API key and model set.")
    except ConfigError as e:
        print(f"Error setting config: {e}")

    print("\nUpdated LLM Settings:")
    print(json.dumps(manager.get_llm_settings().model_dump(mode="json"), indent=2))

    # Example: Get a specific value
    print(f"\nDefault LLM Provider: {manager.get_value('llm_settings.default_provider')}")
    print(f"OpenAI API Key from manager: {manager.get_api_key('openai')}")
    print(f"OpenAI Model from manager: {manager.get_model_name('openai')}")

    # Example: Remove a value (conceptually, sets to default or makes optional field None)
    # print("\nRemoving OpenAI default model (will try to delete key)...")
    # manager.remove_value("llm_settings.providers.openai.default_model")
    # print("\nLLM Settings after attempting removal:")
    # print(json.dumps(manager.get_llm_settings().model_dump(mode="json"), indent=2))
    # print(f"OpenAI Model after removal attempt: {manager.get_model_name('openai')}")
