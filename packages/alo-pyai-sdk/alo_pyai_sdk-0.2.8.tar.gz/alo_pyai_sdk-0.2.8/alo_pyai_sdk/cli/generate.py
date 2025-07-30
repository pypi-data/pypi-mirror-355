import typer
from pathlib import Path
from typing import Optional, List, Any, Dict

from alo_pyai_sdk.core import generator
from alo_pyai_sdk.core import config_manager
from pydantic_ai import models

app = typer.Typer(
    name="generate",
    help="Generate boilerplate code for ALO PyAI SDK components.",
    no_args_is_help=True,
)

AGENT_TEMPLATE_SUBDIR = "fastapi_agent"
AGENT_FILES_STRUCTURE = {
    "main.py": "main.py.j2",
    "agent_definition.py": "agent_definition.py.j2",
    "config.py": "config.py.j2",
    "tools.py": "tools.py.j2",
    "__init__.py": "__init__.py.j2",
}

MCP_CLIENT_TEMPLATE_SUBDIR = "mcp_client"
MCP_CLIENT_FILES_STRUCTURE = {
    "client.py": "client.py.j2",
    "__init__.py": "__init__.py.j2",
}

def _ensure_blank_j2_templates():
    template_dirs_and_structures = [
        (AGENT_TEMPLATE_SUBDIR, AGENT_FILES_STRUCTURE),
        (MCP_CLIENT_TEMPLATE_SUBDIR, MCP_CLIENT_FILES_STRUCTURE),
        ("fastapi_registry", {"__init__.py": "__init__.py.j2"})
    ]
    for template_dir, structure in template_dirs_and_structures:
        if "__init__.py.j2" in structure.values():
            init_j2_path = generator.SDK_TEMPLATE_DIR / template_dir / "__init__.py.j2"
            if not init_j2_path.exists():
                init_j2_path.parent.mkdir(parents=True, exist_ok=True)
                init_j2_path.touch()
_ensure_blank_j2_templates()


@app.command("agent")
def generate_agent(
    name: str = typer.Argument(..., help="The name of the agent. Used for directory and service ID."),
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    llm_config_name: str = typer.Option("mana_llm", "--llm-config", "-l", help="Name of the LLM configuration to use (from alo_config.yaml). This is used by the agent's `settings`."),
    output_type: str = typer.Option("str", "--output-type", "-o", help="Default Pydantic model name for the agent's output (e.g., 'MyOutputModel'). 'str' for plain text output."),
    agent_port: int = typer.Option(0, "--port", "-p", help="Default port for the agent service. 0 for dynamic (not recommended for registry)."),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="A short description for the agent."),
    system_prompt_instructions: Optional[str] = typer.Option(None, "--instructions", "-i", help="Custom system prompt instructions for the agent."),
    ai_assisted: bool = typer.Option(False, "--ai-assisted", help="Enable AI-assisted generation for agent_definition.py custom parts."),
):
    typer.echo(f"Generating agent '{name}'...")
    project_path = Path(project_path_str).resolve()
    
    config_file_path = config_manager.get_config_path(project_path)
    if not config_file_path.exists():
        typer.echo(f"Error: Project not initialized. Config file '{config_file_path}' not found.", err=True)
        typer.echo(f"Please run 'alo-pyai-sdk init {project_path_str}' first.")
        raise typer.Exit(code=1)

    agent_service_id = name.lower().replace(" ", "_").replace("-", "_")
    agents_base_path = project_path / "agents"
    agents_base_path.mkdir(parents=True, exist_ok=True)
    (agents_base_path / "__init__.py").touch(exist_ok=True)
    agent_module_path = agents_base_path / agent_service_id

    if agent_module_path.exists():
        typer.echo(f"Error: Agent directory '{agent_module_path}' already exists.", err=True)
        raise typer.Exit(code=1)
    agent_module_path.mkdir(parents=True, exist_ok=True)
    
    global_cfg = config_manager.load_config(project_path)
    registry_url_val = f"http://{global_cfg.registry.host}:{global_cfg.registry.port}"
    actual_agent_port = agent_port if agent_port != 0 else 8001 

    # Context for Jinja2 rendering if AI-assisted fails or is not used
    base_template_context = {
        "agent_name": name,
        "agent_service_id": agent_service_id,
        "agent_version": "0.1.0", 
        "agent_description": description or f"{name} - An AI Agent service.",
        "agent_port": actual_agent_port,
        "registry_url": registry_url_val,
        "llm_config_name": llm_config_name,
        "llm_model_identifier_fallback": "openai:gpt-4o",
        "agent_system_prompt_instructions": system_prompt_instructions or f"Your primary goal is: {description or 'to assist the user.'}",
        "agent_retries": 1,
    }
    
    # Generate non-agent_definition files first
    other_files_structure = {k: v for k, v in AGENT_FILES_STRUCTURE.items() if k != "agent_definition.py"}
    generator.generate_project_structure(
        project_path=agent_module_path,
        template_subdir=AGENT_TEMPLATE_SUBDIR,
        structure=other_files_structure,
        context=base_template_context,
    )

    agent_def_path = agent_module_path / "agent_definition.py"
    if ai_assisted:
        typer.echo("\nAI-assisted generation for 'agent_definition.py' enabled.")
        try:
            from pydantic_ai import Agent as SdkAgent 
            
            generation_model_instance = _get_llm_for_generation(project_path, llm_config_name)
            code_generation_agent = SdkAgent(model=generation_model_instance, output_type=str)

            typer.echo("Please describe the agent's functionalities for AI to generate the agent_definition.py content:")
            user_purpose_for_ai = description or typer.prompt("1. What is the main purpose/goal of this agent?")
            user_output_desc_for_ai = typer.prompt(f"2. Describe the desired OUTPUT structure. (Default is 'str'. If complex, describe Pydantic model fields/types. Example: 'name: str, age: int')", default="str" if output_type.lower() == "str" else output_type)
            user_deps_desc_for_ai = typer.prompt("3. Describe external DEPENDENCIES. (Default is 'None'. If needed, describe Pydantic model fields/types. Example: 'db_url: str, client_id: str')", default="None")
            user_tools_desc_for_ai = typer.prompt("4. Describe specific TOOLS. (Default is 'None'. List names and what they do. Example: 'get_weather(city: str) -> str: gets weather for a city')", default="None")
            
            generated_output_class_name = f"{name.capitalize().replace('_','')}Output" if user_output_desc_for_ai.lower() != "str" else "str"
            generated_deps_class_name = f"{name.capitalize().replace('_','')}Deps" if user_deps_desc_for_ai.lower() != "none" else "Any"

            ai_prompt = construct_ai_generation_prompt(
                agent_name=name,
                user_purpose=user_purpose_for_ai,
                user_output_desc=user_output_desc_for_ai,
                user_deps_desc=user_deps_desc_for_ai,
                user_tools_desc=user_tools_desc_for_ai,
                generated_output_class_name=generated_output_class_name,
                generated_deps_class_name=generated_deps_class_name,
                # Pass SDK context values needed for the prompt's example structure
                sdk_llm_config_name=llm_config_name,
                sdk_llm_model_identifier_fallback=base_template_context["llm_model_identifier_fallback"],
                sdk_agent_retries=base_template_context["agent_retries"],
                sdk_agent_system_prompt_instructions=base_template_context["agent_system_prompt_instructions"]
            )

            typer.echo("Generating 'agent_definition.py' content using AI. This may take a moment...")
            ai_generated_content = code_generation_agent.run_sync(ai_prompt).output
            
            if ai_generated_content.strip().startswith("```python"):
                 ai_generated_content = ai_generated_content.strip()[9:]
            if ai_generated_content.strip().endswith("```"):
                ai_generated_content = ai_generated_content.strip()[:-3]

            agent_def_path.write_text(ai_generated_content)
            typer.echo(f"AI-generated 'agent_definition.py' written to '{agent_def_path.relative_to(Path.cwd())}'. Please review.")

        except Exception as e:
            typer.echo(f"Error during AI-assisted generation for 'agent_definition.py': {e}", err=True)
            typer.echo("Falling back to standard template for 'agent_definition.py'.")
            generator.render_template(
                template_subdir=AGENT_TEMPLATE_SUBDIR,
                template_name="agent_definition.py.j2",
                output_path=agent_def_path,
                context=base_template_context 
            )
    else:
        generator.render_template(
            template_subdir=AGENT_TEMPLATE_SUBDIR,
            template_name="agent_definition.py.j2",
            output_path=agent_def_path,
            context=base_template_context
        )

    if agent_service_id in global_cfg.agents:
        typer.echo(f"Warning: Agent '{agent_service_id}' already exists in 'alo_config.yaml'. Skipping config update.", color=typer.colors.YELLOW)
    else:
        global_cfg.agents[agent_service_id] = config_manager.AgentServiceConfig(
            service_id=agent_service_id,
            llm_config_name=llm_config_name
        )
        config_manager.save_config(project_path, global_cfg)
        typer.echo(f"Agent '{name}' (service_id: '{agent_service_id}') added to '{config_file_path}'.")

    typer.echo(f"\nAgent '{name}' generated successfully in '{agent_module_path.relative_to(Path.cwd())}'.")
    typer.echo("Next steps:")
    typer.echo(f"1. Review and customize the agent files in '{agent_module_path.relative_to(Path.cwd())}'.")
    if llm_config_name not in global_cfg.llms:
         typer.echo(f"2. IMPORTANT: LLM config '{llm_config_name}' is not yet defined in '{config_file_path}'.", color=typer.colors.RED)
         typer.echo(f"   Please define it using: 'alo-pyai-sdk config llm add --name {llm_config_name} ... --project-path {project_path_str}'", color=typer.colors.RED)
    else:
        typer.echo(f"2. LLM config '{llm_config_name}' will be used (defined in '{config_file_path}').")
    typer.echo(f"3. Run the agent service (after starting the registry): 'cd {project_path_str} && python -m uvicorn agents.{agent_service_id}.main:app --port {actual_agent_port} --reload'")


def construct_ai_generation_prompt(
    agent_name: str,
    user_purpose: str, 
    user_output_desc: str,
    user_deps_desc: str,
    user_tools_desc: str,
    generated_output_class_name: str, 
    generated_deps_class_name: str,
    sdk_llm_config_name: str,
    sdk_llm_model_identifier_fallback: str,
    sdk_agent_retries: int,
    sdk_agent_system_prompt_instructions: str
) -> str:
    
    prompt = f'''You are an expert Python developer creating Pydantic-AI agents for the ALO PyAI SDK.
Your task is to generate the COMPLETE Python code for an 'agent_definition.py' file.
This file should be a fully functional Python module.
Do NOT include any markdown fences (```python ... ```) or any explanatory text outside your Python code.

**Base Structure for `agent_definition.py`:**
The generated file MUST follow this structure closely. Pay attention to imports, class definitions, LLM loading logic, fallbacks, and the final Agent instantiation.

```python
# Expected Imports (add more if your generated tools/models need them)
from pydantic_ai import Agent, RunContext, models
from pydantic import BaseModel, Field
from typing import Type, Any, Optional, List 
from pathlib import Path
import yaml
from pydantic_ai.models.openai import OpenAIModel # Specific example
from pydantic_ai.providers.openai import OpenAIProvider # Specific example
from pydantic_ai.models.test import TestModel

# --- Settings Import with Fallback ---
try:
    from .config import settings
    print(f"INFO: Successfully imported settings from .config for agent '{agent_name}'")
except ImportError:
    print(f"WARNING: Could not import settings from .config for agent '{agent_name}'. Using fallback settings.")
    class FallbackAgentSettings:
        LLM_CONFIG_NAME: str = "{sdk_llm_config_name}" 
        LLM_MODEL_IDENTIFIER_FALLBACK: str = "{sdk_llm_model_identifier_fallback}"
        AGENT_RETRIES: int = {sdk_agent_retries}
        PROJECT_ROOT_PATH: Path = Path(__file__).resolve().parent.parent.parent
    settings = FallbackAgentSettings()
    print(f"INFO: Using fallback settings. LLM_CONFIG_NAME='{{settings.LLM_CONFIG_NAME}}', FallbackModel='{{settings.LLM_MODEL_IDENTIFIER_FALLBACK}}'")

print(f"--- AGENT '{agent_name}' DEFINITION EXECUTION START ---")

# --- LLM Configuration ---
configured_model = None
llm_config_name_to_load = settings.LLM_CONFIG_NAME
project_root = getattr(settings, 'PROJECT_ROOT_PATH', Path(__file__).resolve().parent.parent.parent)
alo_config_path = project_root / "alo_config.yaml"
print(f"INFO: Attempting to load LLM configuration '{{llm_config_name_to_load}}' from '{{alo_config_path}}'")
try:
    with open(alo_config_path, 'r') as f:
        full_config = yaml.safe_load(f)
    if full_config and 'llms' in full_config and llm_config_name_to_load in full_config['llms']:
        llm_conf = full_config['llms'][llm_config_name_to_load]
        print(f"INFO: Found LLM config for '{{llm_config_name_to_load}}': {{llm_conf}}")
        provider_name = llm_conf.get('provider', '').lower()
        api_key = llm_conf.get('api_key')
        model_name_from_config = llm_conf.get('model_name')
        base_url = llm_conf.get('base_url')
        if not provider_name:
            print(f"ERROR: Provider not specified in LLM config '{{llm_config_name_to_load}}'.")
        elif provider_name == 'openai': 
            if not api_key:
                print(f"ERROR: API key not found for OpenAI provider in '{{llm_config_name_to_load}}'.")
            else:
                provider_args = {{"api_key": api_key}}
                if base_url: provider_args["base_url"] = base_url
                openai_provider = OpenAIProvider(**provider_args)
                final_model_name = model_name_from_config or "gpt-4o"
                configured_model = OpenAIModel(model_name=final_model_name, provider=openai_provider)
                print(f"INFO: Successfully configured OpenAIModel: {{final_model_name}}")
        # Add elif blocks here for other providers if specified by user and you know how
        else:
            print(f"WARNING: Direct loader for provider '{{provider_name}}' is not implemented. Will attempt fallback.")
    else:
        print(f"WARNING: LLM config '{{llm_config_name_to_load}}' not found or 'llms' key missing in {{alo_config_path}}.")
except FileNotFoundError:
    print(f"ERROR: alo_config.yaml not found at {{alo_config_path}}")
except yaml.YAMLError as e:
    print(f"ERROR: Error parsing alo_config.yaml: {{e}}")
except Exception as e:
    print(f"ERROR: Unexpected error during direct LLM config loading: {{e}}")

if not configured_model:
    print(f"INFO: Direct LLM loading failed/skipped. Falling back to infer_model with: {{settings.LLM_MODEL_IDENTIFIER_FALLBACK}}")
    try:
        configured_model = models.infer_model(settings.LLM_MODEL_IDENTIFIER_FALLBACK)
        if configured_model: print(f"INFO: Successfully fell back to LLM via infer_model: {{settings.LLM_MODEL_IDENTIFIER_FALLBACK}}")
        else: print(f"WARNING: Fallback models.infer_model returned None for {{settings.LLM_MODEL_IDENTIFIER_FALLBACK}}.")
    except Exception as fallback_e:
        print(f"ERROR: Error during fallback model inference: {{fallback_e}}")

if not configured_model:
    print(f"CRITICAL: All LLM config attempts failed for agent '{agent_name}'. Initializing with TestModel.")
    configured_model = TestModel()
    print(f"INFO: Agent '{agent_name}' initialized with TestModel.")

# --- Define Agent Output Type ---
# Based on: "{user_output_desc}"
# If not 'str', define class {generated_output_class_name}(BaseModel) here.
# Assign the class or 'str' to _output_type_actual.
_output_type_actual: Type[Any] = str # Default, modify if user_output_desc is not 'str'
# <<< IF user_output_desc IS NOT 'str', DEFINE {generated_output_class_name} AND SET _output_type_actual HERE >>>

# --- Define Agent Dependencies Type ---
# Based on: "{user_deps_desc}"
# If not 'None', define class {generated_deps_class_name}(BaseModel) here.
# Assign the class or 'Any' to _deps_type_actual.
_deps_type_actual: Type[Any] = Any # Default, modify if user_deps_desc is not 'None'
# <<< IF user_deps_desc IS NOT 'None', DEFINE {generated_deps_class_name} AND SET _deps_type_actual HERE >>>

print(f"INFO: Agent '{agent_name}' output type: {{{_output_type_actual}}}")
print(f"INFO: Agent '{agent_name}' dependencies type: {{{_deps_type_actual}}}")

# --- Load MCP Servers ---
mcp_servers_list: List[models.MCPServer] = []
print(f"INFO: Attempting to load MCP servers from project root: {{project_root}}")
try:
    from alo_pyai_sdk.core.llm_loader import load_mcp_servers_from_project_config
    mcp_servers_list = load_mcp_servers_from_project_config(project_root)
    if mcp_servers_list: print(f"INFO: Agent '{agent_name}' loaded {{len(mcp_servers_list)}} MCP server(s).")
    else: print(f"INFO: No MCP servers configured/loaded for agent '{agent_name}'.")
except ImportError:
    print("WARNING: Could not import load_mcp_servers_from_project_config. MCP servers disabled.")
except Exception as e:
    print(f"WARNING: Could not load MCP servers for agent '{agent_name}': {{e}}")

# --- Define Tools (if any) ---
# Based on: "{user_tools_desc}"
# Define tool functions here if requested.
agent_tools_list = [] # Default to no tools
# <<< IF user_tools_desc IS NOT 'None', DEFINE TOOL FUNCTIONS AND POPULATE agent_tools_list HERE >>>
# Example:
# async def example_tool_func(ctx: RunContext[Any], param: str) -> str:
#     """Docstring for example_tool_func."""
#     return f"Tool processed {{{{param}}}}" # Escaped for f-string
# agent_tools_list = [example_tool_func]

# --- System Prompt ---
# User purpose: "{user_purpose}"
# Extra instructions: "{user_instructions_extra}"
final_system_prompt = f"""You are '{agent_name}', an AI assistant. {user_purpose}.
{user_instructions_extra if user_instructions_extra and user_instructions_extra.lower() != 'none' else ''}""".strip()
print(f"INFO: Agent '{agent_name}' system prompt (first 100 chars): \"{{final_system_prompt[:100].replace('\\n', ' ')}}...\"")

# --- Create Agent Instance ---
print(f"INFO: Creating Pydantic-AI Agent '{agent_name}' instance...")
agent = Agent(
    model=configured_model,
    output_type=_output_type_actual,
    deps_type=_deps_type_actual,
    system_prompt=final_system_prompt,
    tools=agent_tools_list,
    retries=settings.AGENT_RETRIES,
)
print(f"INFO: Pydantic-AI Agent '{agent_name}' instance created successfully.")

# --- Main Agent Accessor ---
def get_agent() -> Agent:
    return agent

if __name__ == "__main__":
    print(f"--- Running '{agent_name}' agent_definition.py directly (__main__) ---")
    print(f"Settings LLM Config Name: {{settings.LLM_CONFIG_NAME}}")
    if configured_model: model_details = getattr(configured_model, 'model_name', str(type(configured_model))); print(f"Final Configured Model: {{model_details}}")
    else: print("Final Configured Model: ERROR - NOT SET")
    print(f"Agent Output Type: {{{_output_type_actual}}}")
    print(f"Agent Dependencies Type: {{{_deps_type_actual}}}")
    print(f"Agent Retries: {{agent.retries}}")
    tool_names = [t.name for t in agent.tools] if agent.tools else "None"; print(f"Agent Tools: {{tool_names}}")
    mcp_server_details = [getattr(s, 'url', getattr(s, 'command', str(s))) for s in agent.mcp_servers] if agent.mcp_servers else "None"; print(f"Agent MCP Servers: {{mcp_server_details}}")
    pass

print(f"--- AGENT '{agent_name}' DEFINITION EXECUTION END ---")
```

**User-Provided Information for this generation:**
- Agent Name: `{agent_name}`
- Main Purpose/Goal: `{user_purpose}`
- Desired Output Structure: `{user_output_desc}` (Target class name if not str: `{generated_output_class_name}`)
- External Dependencies: `{user_deps_desc}` (Target class name if not None: `{generated_deps_class_name}`)
- Additional System Prompt Instructions: `{user_instructions_extra}`
- Specific Tools: `{user_tools_desc}`

**Your Task:**
Fill in the `<<< ... >>>` placeholders in the Python code structure above based on the "User-Provided Information".
- If `user_output_desc` is "str" (case-insensitive), the `_output_type_actual` should remain `str`. Otherwise, define the class `{generated_output_class_name}` and assign it to `_output_type_actual`.
- If `user_deps_desc` is "none" (case-insensitive) or empty, `_deps_type_actual` should remain `Any`. Otherwise, define the class `{generated_deps_class_name}` and assign it to `_deps_type_actual`.
- If `user_tools_desc` is "none" (case-insensitive) or empty, `agent_tools_list` should remain `[]`. Otherwise, define the tool functions and assign them to `agent_tools_list`.
Ensure all necessary imports for your generated models/tools are included at the top.
The Jinja2 placeholders `{{{{ ... }}}}` in the Python code structure are for the SDK's templating engine and should be kept as is. Your generated code will replace the `<<< ... >>>` placeholders.
Output ONLY the complete Python code.
'''
    return prompt

def _get_llm_for_generation(project_path: Path, llm_config_name_for_gen: Optional[str]) -> models.Model:
    from alo_pyai_sdk.core.llm_loader import get_pydantic_ai_model as get_sdk_llm_internal
    
    global_cfg = config_manager.load_config(project_path)
    
    if llm_config_name_for_gen and llm_config_name_for_gen in global_cfg.llms:
        return get_sdk_llm_internal(llm_config_name_for_gen, project_path)
    elif "mana_llm" in global_cfg.llms:
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found for AI generation. Falling back to 'mana_llm'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal("mana_llm", project_path)
    elif "default_openai" in global_cfg.llms: 
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found for AI generation. Falling back to 'default_openai'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal("default_openai", project_path)
    elif global_cfg.llms: 
        first_config_name = list(global_cfg.llms.keys())[0]
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found. Falling back to first available: '{first_config_name}'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal(first_config_name, project_path)
    else:
        typer.echo(f"Error: No LLM configurations found in '{config_manager.get_config_path(project_path)}'. Cannot use AI-assisted generation.", err=True)
        typer.echo("Attempting to use 'openai:gpt-4o' as a last resort for generation, ensure OPENAI_API_KEY is set in environment.", color=typer.colors.YELLOW)
        return models.infer_model("openai:gpt-4o")

@app.command("mcp-client")
def generate_mcp_client(
    name: str = typer.Argument(..., help="The name for the MCP client module."),
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    server_url: str = typer.Option("http://localhost:3001/sse", "--server-url", help="The URL of the MCP server."),
    transport_type: str = typer.Option("sse", "--transport", help="MCP transport type (sse, streamable-http, stdio)."),
    command: Optional[str] = typer.Option(None, "--command", help="Command for stdio transport."),
    args_str: Optional[str] = typer.Option(None, "--args", help="Comma-separated arguments for stdio command."),
    tool_prefix: Optional[str] = typer.Option(None, "--tool-prefix", help="Prefix for tools from this MCP server."),
):
    """
    Generates a Python module for an MCP client.
    """
    typer.echo(f"Generating MCP client module '{name}' for server URL '{server_url}'...")
    project_path = Path(project_path_str).resolve()
    client_module_name = name.lower().replace(" ", "_").replace("-", "_")
    
    clients_base_path = project_path / "mcp_clients"
    clients_base_path.mkdir(parents=True, exist_ok=True)
    (clients_base_path / "__init__.py").touch(exist_ok=True)

    client_file_path = clients_base_path / f"{client_module_name}.py" 

    if client_file_path.exists():
        typer.echo(f"Error: MCP client file '{client_file_path}' already exists.", err=True)
        raise typer.Exit(code=1)

    args_list: Optional[List[str]] = args_str.split(',') if args_str else None

    context = {
        "client_name": name,
        "server_url": server_url,
        "transport_type": transport_type,
        "command": command,
        "args_list": args_list or [],
        "tool_prefix": tool_prefix,
    }
    
    generator.render_template(
        template_subdir=MCP_CLIENT_TEMPLATE_SUBDIR,
        template_name="client.py.j2",
        output_path=client_file_path,
        context=context,
    )

    global_cfg = config_manager.load_config(project_path)
    if client_module_name in global_cfg.mcp_clients:
        typer.echo(f"Warning: MCP client configuration '{client_module_name}' already exists in 'alo_config.yaml'. Skipping automatic addition.", color=typer.colors.YELLOW)
    else:
        factory_function_name = f"get_{client_module_name}_mcp_server"
        mcp_client_config = config_manager.MCPClientConfig(
            module=f"mcp_clients.{client_module_name}",
            factory_function=factory_function_name,
            type=transport_type,
            url=server_url if transport_type in ["sse", "streamable-http"] else None,
            command=command if transport_type == "stdio" else None,
            args=args_list if transport_type == "stdio" else None,
            tool_prefix=tool_prefix
        )
        global_cfg.mcp_clients[client_module_name] = mcp_client_config
        config_manager.save_config(project_path, global_cfg)
        typer.echo(f"MCP client '{client_module_name}' configuration added to 'alo_config.yaml'.")
    
    typer.echo(f"MCP client module '{name}' generated successfully at '{client_file_path.relative_to(Path.cwd())}'.")
    typer.echo("Next steps:")
    typer.echo(f"1. Review and customize the client module '{client_file_path.relative_to(Path.cwd())}'.")
    typer.echo(f"2. The client has been automatically configured in 'alo_config.yaml'. You can now reference '{client_module_name}' in your agent configurations.")

if __name__ == "__main__":
    app()

</final_file_content>

IMPORTANT: For any future changes to this file, use the final_file_content shown above as your reference. This content reflects the current state of the file, including any auto-formatting (e.g., if you used single quotes but the formatter converted them to double quotes). Always base your SEARCH/REPLACE operations on this final version to ensure accuracy.

<environment_details>
# VSCode Visible Files
alo_pyai_sdk/cli/generate.py

# VSCode Open Tabs
alo_pyai_sdk/cli/__init__.py
alo_pyai_sdk/core/__init__.py
pyproject.toml
alo_pyai_sdk/cli/configure.py
alo_pyai_sdk/__init__.py
alo_pyai_sdk/templates/fastapi_agent/agent_definition.py.j2
alo_pyai_sdk/cli/generate.py
alo_pyai_sdk/templates/fastapi_agent/config.py.j2
alo_pyai_sdk/templates/fastapi_agent/main.py.j2
alo_pyai_sdk/cli/run_commands.py
alo_pyai_sdk/cli/main.py
alo_pyai_sdk/core/config_manager.py
alo_pyai_sdk/core/llm_loader.py
README.md
alo_pyai_sdk/templates/fastapi_registry/__init__.py.j2
alo_pyai_sdk/cli/registry_commands.py
alo_pyai_sdk/cli/provision_commands.py

# Current Time
15/06/2025, 3:55:41 pm (Europe/Rome, UTC+2:00)

# Context Window Usage
536,530 / 1,048.576K tokens used (51%)

# Current Mode
ACT MODE
</environment_details>
