import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl

# --- Configuration Models ---

class LLMConfig(BaseModel):
    provider: str
    api_key: str = Field(..., repr=False) # Hide API key in repr
    model_name: Optional[str] = None
    # Add other common LLM params like temperature, max_tokens if needed globally

class MCPClientConfig(BaseModel):
    type: str = "stdio" # stdio, sse, streamable-http
    url: Optional[HttpUrl] = None # For sse, streamable-http
    command: Optional[str] = None # For stdio
    args: Optional[List[str]] = None # For stdio
    tool_prefix: Optional[str] = None

class AgentServiceConfig(BaseModel):
    service_id: str # Name of the agent
    llm_config_name: str # Key to an LLMConfig in the main config
    # service_url will be dynamically registered or configured during 'generate agent'
    # Other agent-specific metadata can be added here
    # e.g., description, skills, default_output_type

class RegistryConfig(BaseModel):
    host: str = "localhost"
    port: int = 8000

class GlobalConfig(BaseModel):
    llms: Dict[str, LLMConfig] = Field(default_factory=dict)
    mcp_servers: Dict[str, MCPClientConfig] = Field(default_factory=dict)
    agents: Dict[str, AgentServiceConfig] = Field(default_factory=dict)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)

# --- Configuration Management ---

CONFIG_FILE_NAME = "alo_config.yaml"

def get_config_path(project_path: Path) -> Path:
    """Determines the path to the configuration file within a project."""
    return project_path / CONFIG_FILE_NAME

def load_config(project_path: Path) -> GlobalConfig:
    """Loads the global configuration from the project's config file."""
    config_path = get_config_path(project_path)
    if not config_path.exists():
        return GlobalConfig()  # Return default empty config if file doesn't exist
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    return GlobalConfig(**raw_config if raw_config else {})

def save_config(project_path: Path, config: GlobalConfig) -> None:
    """Saves the global configuration to the project's config file."""
    config_path = get_config_path(project_path)
    config_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    with open(config_path, "w") as f:
        yaml.dump(config.model_dump(exclude_none=True), f, sort_keys=False)

# --- Helper functions for CLI commands (to be expanded) ---

def add_llm_config(project_path: Path, name: str, provider: str, api_key: str, model_name: Optional[str]):
    config = load_config(project_path)
    if name in config.llms:
        print(f"Error: LLM configuration '{name}' already exists.", file=sys.stderr) # type: ignore
        # Consider raising an error or asking to overwrite
        return
    config.llms[name] = LLMConfig(provider=provider, api_key=api_key, model_name=model_name)
    save_config(project_path, config)
    print(f"LLM configuration '{name}' added.")

def list_llm_configs(project_path: Path):
    config = load_config(project_path)
    if not config.llms:
        print("No LLM configurations found.")
        return
    print("Available LLM Configurations:")
    for name, llm_conf in config.llms.items():
        print(f"  - {name}: Provider={llm_conf.provider}, Model={llm_conf.model_name or 'Default'}")

# Similar functions for mcp_servers and agents will be added here.

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    import sys
    example_project_path = Path(".") / "temp_alo_project"
    example_project_path.mkdir(exist_ok=True)

    # Test saving
    cfg = GlobalConfig()
    cfg.llms["my_openai"] = LLMConfig(provider="openai", api_key="sk-test", model_name="gpt-4o")
    cfg.mcp_servers["py_runner"] = MCPClientConfig(type="stdio", command="deno run ...")
    cfg.agents["test_agent"] = AgentServiceConfig(service_id="test_agent", llm_config_name="my_openai")
    save_config(example_project_path, cfg)
    print(f"Saved example config to {get_config_path(example_project_path)}")

    # Test loading
    loaded_cfg = load_config(example_project_path)
    print("\nLoaded config:")
    print(f"LLMs: {loaded_cfg.llms}")
    print(f"MCP Servers: {loaded_cfg.mcp_servers}")
    print(f"Agents: {loaded_cfg.agents}")
    print(f"Registry: {loaded_cfg.registry}")

    # Test CLI helper
    add_llm_config(example_project_path, "another_llm", "anthropic", "sk-ant-test", "claude-3")
    list_llm_configs(example_project_path)
    
    # Clean up
    # import shutil
    # shutil.rmtree(example_project_path)
