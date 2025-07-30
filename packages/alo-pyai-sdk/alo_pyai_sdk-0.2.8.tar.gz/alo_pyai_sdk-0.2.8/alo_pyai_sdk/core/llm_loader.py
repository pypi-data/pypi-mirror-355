from pathlib import Path
from typing import Any, Type, Dict # Added Dict
from pathlib import Path
from typing import Any, Type, Dict, List # Added List
from pydantic_ai import models # Keep for infer_model and base Model type
from pydantic_ai.mcp import MCPServer # Added for MCP server loading
import importlib # Added for dynamic imports

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
        if "mana_llm" in global_config.llms: # Check for mana_llm first
            llm_config_name = "mana_llm"
        elif "default_openai" in global_config.llms: # Then check for default_openai as a secondary fallback
            llm_config_name = "default_openai"
        elif global_config.llms: # Then any other available
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

def load_mcp_servers_from_project_config(project_root: Path) -> List[MCPServer]:
    """
    Loads MCP client configurations from the project's alo_config.yaml,
    instantiates them using their factory functions, and returns a list of MCPServer instances.
    """
    global_config = config_manager.load_config(project_root)
    mcp_server_instances: List[MCPServer] = []

    if not global_config.mcp_clients:
        return []

    for client_name, client_config in global_config.mcp_clients.items():
        if client_config.module and client_config.factory_function:
            try:
                module_path = client_config.module
                # Ensure the module path is absolute if it's coming from project structure
                # For now, assume it's correctly specified relative to PYTHONPATH
                # e.g. "mcp_clients.my_client_module"
                
                # Dynamically import the module
                # If project_root is not in sys.path, relative imports from project might fail
                # This assumes that the 'mcp_clients' dir is in a location findable by Python's import system
                # or that the project_root is added to sys.path by the caller or environment.
                # For CLI usage where CWD is project_root, this should generally work.
                module = importlib.import_module(module_path)
                
                factory_func = getattr(module, client_config.factory_function)
                
                # Call the factory function with parameters if any
                if client_config.parameters:
                    mcp_server_instance = factory_func(**client_config.parameters)
                else:
                    mcp_server_instance = factory_func()
                
                if not isinstance(mcp_server_instance, MCPServer):
                    print(f"Warning: Factory function '{client_config.factory_function}' in module '{module_path}' for MCP client '{client_name}' did not return an MCPServer instance. Skipping.")
                    continue
                
                # If the MCPServerStdio or similar needs its tool_prefix set from config,
                # and the factory doesn't handle it, we might need to set it here.
                # However, the generated client.py.j2 template already uses the tool_prefix.
                # If client_config.tool_prefix is set and differs from instance, it's ambiguous.
                # For now, assume factory handles it or it's set on instance.
                if client_config.tool_prefix and hasattr(mcp_server_instance, 'tool_prefix') and mcp_server_instance.tool_prefix != client_config.tool_prefix:
                     # This could happen if the factory sets a default and config also has one.
                     # Or if the factory doesn't take tool_prefix and we want to override.
                     # For now, we'll prefer the one from the config if the instance allows setting it.
                    try:
                        # Check if tool_prefix is a settable property or attribute
                        if hasattr(type(mcp_server_instance), 'tool_prefix') and isinstance(getattr(type(mcp_server_instance), 'tool_prefix'), property) and getattr(type(mcp_server_instance), 'tool_prefix').fset is not None:
                             setattr(mcp_server_instance, 'tool_prefix', client_config.tool_prefix)
                        elif hasattr(mcp_server_instance, 'tool_prefix'): # direct attribute
                             mcp_server_instance.tool_prefix = client_config.tool_prefix
                        # else: cannot set, rely on factory
                    except AttributeError:
                        pass # Cannot set it, rely on what the factory did.


                mcp_server_instances.append(mcp_server_instance)
                
            except ImportError:
                print(f"Warning: Could not import module '{client_config.module}' for MCP client '{client_name}'. Skipping.")
            except AttributeError:
                print(f"Warning: Could not find factory function '{client_config.factory_function}' in module '{client_config.module}' for MCP client '{client_name}'. Skipping.")
            except Exception as e:
                print(f"Warning: Error instantiating MCP client '{client_name}' from module '{client_config.module}': {e}. Skipping.")
        elif client_config.type: # Handle direct configuration if module/factory not present
            # This part would instantiate MCPServerStdio, MCPServerSSE etc. directly
            # based on client_config.type and other parameters.
            # For now, we focus on the generated module/factory approach.
            # print(f"Note: Direct MCP client configuration for '{client_name}' (type: {client_config.type}) is not yet fully implemented for loading in agents, use generated clients.")
            pass


    return mcp_server_instances
