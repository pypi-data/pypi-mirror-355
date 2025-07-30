from pathlib import Path
from typing import Any, Type, Dict # Added Dict
from pydantic_ai import models # Keep for infer_model and base Model type

# Import Models
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.models.bedrock import BedrockConverseModel

# Import Providers
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from pydantic_ai.providers.google import GoogleProvider # For GoogleModel with Vertex
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.cohere import CohereProvider
from pydantic_ai.providers.bedrock import BedrockProvider

from . import config_manager # Use relative import for core modules

def get_pydantic_ai_model(llm_config_name: str, project_root: Path) -> models.Model:
    """
    Loads the specified LLM configuration from the project's alo_config.yaml
    located at project_root and returns an initialized Pydantic-AI Model instance.
    This version is intended for use by the SDK CLI itself.
    """
    global_config = config_manager.load_config(project_root)
    
    if llm_config_name not in global_config.llms:
        # Try to find a default or raise error
        if "default_openai" in global_config.llms:
            llm_config_name = "default_openai"
        elif global_config.llms:
            llm_config_name = list(global_config.llms.keys())[0]
        else:
            raise ValueError(f"LLM configuration '{llm_config_name}' not found and no fallbacks available in alo_config.yaml at {project_root}.")
        
    llm_conf = global_config.llms[llm_config_name]
    
    provider_key = llm_conf.provider.lower()

    # Map provider strings to their Model and Provider classes
    provider_class_map: Dict[str, Dict[str, Type]] = {
        "openai": {"model": OpenAIModel, "provider_sdk": OpenAIProvider},
        "anthropic": {"model": AnthropicModel, "provider_sdk": AnthropicProvider},
        "google-gla": {"model": GeminiModel, "provider_sdk": GoogleGLAProvider},
        "google-vertex": {"model": GoogleModel, "provider_sdk": GoogleProvider}, 
        "groq": {"model": GroqModel, "provider_sdk": GroqProvider},
        "mistral": {"model": MistralModel, "provider_sdk": MistralProvider},
        "cohere": {"model": CohereModel, "provider_sdk": CohereProvider},
        "bedrock": {"model": BedrockConverseModel, "provider_sdk": BedrockProvider},
    }
    
    model_class_info = provider_class_map.get(provider_key)
    model_class = model_class_info.get("model") if model_class_info else None
    
    model_args: dict[str, Any] = {}
    actual_model_name = llm_conf.model_name # This should be the specific model like 'gpt-4o'

    # Prepare provider arguments if API key or other specifics are needed
    if model_class_info and model_class_info.get("provider_sdk"):
        provider_sdk_class = model_class_info["provider_sdk"]
        provider_init_args: dict[str, Any] = {}
        
        # Common arguments
        if llm_conf.api_key:
            provider_init_args["api_key"] = llm_conf.api_key
        if llm_conf.base_url and provider_key in ["openai", "mistral", "deepseek"]: # Providers known to take base_url
             provider_init_args["base_url"] = llm_conf.base_url
        
        # Provider-specific arguments
        if provider_key == "google-vertex":
            # GoogleProvider (for google-genai SDK) takes project, location, credentials
            # We assume project_id and region from extra_args map to project and location
            project_arg = llm_conf.extra_args.get("project_id") if llm_conf.extra_args else None
            location_arg = llm_conf.extra_args.get("region") if llm_conf.extra_args else None
            if project_arg: provider_init_args["project"] = project_arg
            if location_arg: provider_init_args["location"] = location_arg
            # For GoogleProvider, also set vertexai=True
            provider_init_args["vertexai"] = True
            if not actual_model_name: actual_model_name = "gemini-1.5-pro" # Default for vertex
        elif provider_key == "bedrock":
            # BedrockProvider takes aws specific args like region_name, access_key_id etc.
            # These would typically come from llm_conf.extra_args or environment
            if llm_conf.extra_args:
                aws_args = {k: v for k, v in llm_conf.extra_args.items() if k in ["region_name", "aws_access_key_id", "aws_secret_access_key", "aws_session_token", "profile_name"]}
                provider_init_args.update(aws_args)
            if not actual_model_name: actual_model_name = "anthropic.claude-3-5-sonnet-latest" # A Bedrock default

        if provider_init_args or provider_key in ["google-gla", "google-vertex", "bedrock", "openai"]: # Some providers can be init'd without args
            try:
                # For google-gla, GoogleGLAProvider is parameterless if API key is in env
                if provider_key == "google-gla" and not llm_conf.api_key:
                     model_args["provider"] = GoogleGLAProvider()
                elif provider_key == "openai" and not llm_conf.api_key and not llm_conf.base_url: # OpenAIProvider can be parameterless
                     model_args["provider"] = OpenAIProvider()
                else:
                    model_args["provider"] = provider_sdk_class(**provider_init_args)
            except Exception as e:
                print(f"Warning: Could not initialize provider {provider_sdk_class.__name__} with args {provider_init_args}: {e}. Relying on infer_model.")
                # Clear model_args["provider"] so infer_model is used without a pre-set provider if init fails
                if "provider" in model_args: del model_args["provider"]


    if not actual_model_name: # Fallback model name if not set
        if provider_key == "openai": actual_model_name = "gpt-4o"
        elif provider_key == "anthropic": actual_model_name = "claude-3-5-sonnet-latest"
        elif provider_key == "google-gla": actual_model_name = "gemini-1.5-flash"
        else: actual_model_name = "default" # This might cause issues if not a valid model for the provider

    if model_class:
        try:
            return model_class(model_name=actual_model_name, **model_args)
        except Exception as e:
            # Fallback to infer_model if direct instantiation fails (e.g. missing model_name for some providers)
            print(f"Warning: Could not directly instantiate {model_class} with name '{actual_model_name}' and args {model_args}: {e}. Falling back to infer_model.")
            pass # Fall through to infer_model

    # Fallback to infer_model for unmapped providers or if direct instantiation failed
    # This relies on Pydantic-AI's internal mechanisms and environment variables for API keys if not passed via provider
    model_identifier = f"{llm_conf.provider}:{actual_model_name}" if actual_model_name != "default" else llm_conf.provider
    if "provider" in model_args: # If we created a provider instance, try to use it with infer_model
        return models.infer_model(model_identifier, provider=model_args["provider"])
    
    return models.infer_model(model_identifier)
