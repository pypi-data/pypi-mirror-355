from pathlib import Path
from typing import Any
from pydantic_ai import models

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
    
    provider_map = {
        "openai": models.OpenAIModel,
        "anthropic": models.AnthropicModel,
        "google-gla": models.GeminiModel,
        "google-vertex": models.GeminiModel, # Needs specific provider setup
        "groq": models.GroqModel,
        "mistral": models.MistralModel,
        "cohere": models.CohereModel,
        "bedrock": models.BedrockConverseModel,
    }
    
    model_class = provider_map.get(llm_conf.provider.lower())
    
    model_args: dict[str, Any] = {}
    actual_model_name = llm_conf.model_name # This should be the specific model like 'gpt-4o'

    # Prepare provider arguments if API key or other specifics are needed
    if llm_conf.provider.lower() in ["openai", "anthropic", "cohere", "groq", "mistral", "google-gla"]:
        provider_name_cap = llm_conf.provider.capitalize()
        # For google-gla, Pydantic-AI uses GeminiModel with GoogleGLAProvider
        if llm_conf.provider.lower() == "google-gla":
            provider_name_cap = "GoogleGLA" # Matches Pydantic-AI's provider name
        
        provider_class = getattr(models, f"{provider_name_cap}Provider", None)
        if provider_class:
            provider_init_args: dict[str, Any] = {}
            if llm_conf.api_key:
                provider_init_args["api_key"] = llm_conf.api_key
            if llm_conf.base_url and hasattr(provider_class, "__init__") and "base_url" in provider_class.__init__.__annotations__:
                 provider_init_args["base_url"] = llm_conf.base_url
            
            if provider_init_args: # Only instantiate if there are args, otherwise let infer_model handle it
                try:
                    model_args["provider"] = provider_class(**provider_init_args)
                except Exception as e:
                    print(f"Warning: Could not initialize provider {provider_name_cap} with args {provider_init_args}: {e}. Relying on infer_model.")


    if llm_conf.provider.lower() == "google-vertex":
        # Vertex AI needs special handling for project_id and region
        project_id = llm_conf.extra_args.get("project_id") if llm_conf.extra_args else None
        region = llm_conf.extra_args.get("region") if llm_conf.extra_args else None
        provider_instance = models.GoogleVertexProvider(project_id=project_id, region=region)
        model_args["provider"] = provider_instance
        if not actual_model_name: actual_model_name = "gemini-1.5-pro" # Default for vertex

    if not actual_model_name: # Fallback model name if not set
        if llm_conf.provider.lower() == "openai": actual_model_name = "gpt-4o"
        elif llm_conf.provider.lower() == "anthropic": actual_model_name = "claude-3-5-sonnet-latest"
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
