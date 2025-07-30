import os
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field, FilePath, DirectoryPath
from pathlib import Path

# --- LLM Provider Specific Settings ---
class OpenAIConfig(BaseModel):
    api_key: Optional[str] = Field(None, description="OpenAI API key.")
    default_model: Optional[str] = Field("gpt-3.5-turbo", description="Default model for OpenAI.")

class AnthropicConfig(BaseModel):
    api_key: Optional[str] = Field(None, description="Anthropic API key.")
    default_model: Optional[str] = Field("claude-3-haiku-20240307", description="Default model for Anthropic.") # Updated to a common Haiku model

class GeminiConfig(BaseModel):
    api_key: Optional[str] = Field(None, description="Gemini API key (for Google AI Studio).")
    # For Vertex AI, authentication is usually handled via gcloud ADC.
    # We might need a flag or different structure if supporting Vertex AI specifically.
    default_model: Optional[str] = Field("gemini-1.5-flash-latest", description="Default model for Gemini.")


# --- LLM Settings ---
class LLMProviderSettings(BaseModel):
    openai: Optional[OpenAIConfig] = Field(default_factory=OpenAIConfig)
    anthropic: Optional[AnthropicConfig] = Field(default_factory=AnthropicConfig)
    gemini: Optional[GeminiConfig] = Field(default_factory=GeminiConfig)
    # Add other providers here as they are supported

class LLMSettings(BaseModel):
    default_provider: Optional[Literal["openai", "anthropic", "gemini"]] = Field("openai", description="Default LLM provider to use if not specified elsewhere.")
    default_model_name: Optional[str] = Field(None, description="Global default model name if a provider-specific default is not set (less common).")
    providers: LLMProviderSettings = Field(default_factory=LLMProviderSettings)

# --- Main SDK Configuration ---
class SDKConfig(BaseModel):
    version: str = Field("1.0", description="Configuration file version.")
    llm_settings: LLMSettings = Field(default_factory=LLMSettings)
    # Other global SDK settings can be added here in the future

    @staticmethod
    def get_default_config_path() -> Path:
        # ~/.alo/config.json
        return Path.home() / ".alo" / "config.json"

    @staticmethod
    def get_xdg_config_path() -> Path:
        # ~/.config/alo/config.json (for XDG compliance)
        config_home = os.getenv("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "alo" / "config.json"
        return Path.home() / ".config" / "alo" / "config.json"
    
    @classmethod
    def get_active_config_path(cls) -> Path:
        # Prefer XDG path if it exists or if XDG_CONFIG_HOME is set, otherwise use ~/.alo
        # For simplicity in this phase, we'll just use ~/.alo/config.json
        # but a more robust solution would check XDG.
        # Let's use a simpler default for now and refine later if needed.
        return cls.get_default_config_path()
