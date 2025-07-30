import typer
from pathlib import Path
from typing import Optional, List, Any, Dict

from alo_pyai_sdk.core import generator
from alo_pyai_sdk.core import config_manager

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
    llm_config_name: str = typer.Option("default_openai", "--llm-config", "-l", help="Name of the LLM configuration to use (from alo_config.yaml) for the agent itself AND for AI-assisted generation if used."),
    output_type: str = typer.Option("str", "--output-type", "-o", help="Default Pydantic model name for the agent's output (e.g., 'MyOutputModel'). 'str' for plain text."),
    agent_port: int = typer.Option(0, "--port", "-p", help="Default port for the agent service. 0 for dynamic (not recommended for registry)."),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="A short description for the agent."),
    system_prompt_instructions: Optional[str] = typer.Option(None, "--instructions", "-i", help="Custom system prompt instructions for the agent."),
    ai_assisted: bool = typer.Option(False, "--ai-assisted", help="Enable AI-assisted generation for agent_definition.py."),
):
    """
    Generates a new agent service with a FastAPI app and Pydantic-AI agent definition.
    Assumes an 'alo_config.yaml' exists in the project_path.
    """
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

    context = {
        "agent_name": name,
        "agent_service_id": agent_service_id,
        "agent_version": "0.1.0", 
        "agent_description": description or f"{name} - An AI Agent service.",
        "agent_port": actual_agent_port,
        "registry_url": registry_url_val,
        "llm_config_name": llm_config_name,
        "llm_model_identifier_fallback": "openai:gpt-4o", 
        "agent_output_type": output_type if output_type.lower() != "str" else f"{name.capitalize().replace('_','')}Output",
        "agent_output_type_is_str": output_type.lower() == "str",
        "agent_deps_type": "Any", 
        "agent_system_prompt_instructions": system_prompt_instructions or f"You are {name}, an AI assistant. Please assist the user.",
    }
    
    generator.generate_project_structure(
        project_path=agent_module_path,
        template_subdir=AGENT_TEMPLATE_SUBDIR,
        structure=AGENT_FILES_STRUCTURE,
        context=context,
    )

    if ai_assisted:
        typer.echo("\nAI-assisted generation for 'agent_definition.py' enabled.")
        try:
            # Use the SDK's own config loader and pydantic_ai Agent for generation
            from pydantic_ai import Agent as SdkAgent # Alias to avoid conflict
            from alo_pyai_sdk.core.llm_loader import get_pydantic_ai_model as get_sdk_llm

            sdk_llm_config_name = llm_config_name # Use the same LLM config for generation for now
            
            # Check if the chosen LLM config for generation exists in the project
            if sdk_llm_config_name not in global_cfg.llms:
                # Fallback or error if the generation LLM config is not found
                # For simplicity, let's try a common default or raise an error.
                # A more robust solution might prompt the user or have a dedicated SDK default.
                if "default_openai" in global_cfg.llms:
                    sdk_llm_config_name = "default_openai"
                    typer.echo(f"Warning: LLM config '{llm_config_name}' not found for AI generation. Falling back to 'default_openai'.", color=typer.colors.YELLOW)
                elif global_cfg.llms: # pick the first one if default_openai is not there
                    sdk_llm_config_name = list(global_cfg.llms.keys())[0]
                    typer.echo(f"Warning: LLM config '{llm_config_name}' not found for AI generation. Falling back to '{sdk_llm_config_name}'.", color=typer.colors.YELLOW)
                else:
                    typer.echo(f"Error: No LLM configurations found in '{config_file_path}'. Cannot use AI-assisted generation.", err=True)
                    typer.echo(f"Please add an LLM config first: alo-pyai-sdk config llm add --name your_llm_config ... --project-path {project_path_str}")
                    raise typer.Exit(code=1)
            
            generation_model_instance = get_sdk_llm(sdk_llm_config_name, project_path)
            generation_agent = SdkAgent(model=generation_model_instance, output_type=str)

            typer.echo("Please describe the agent's functionalities:")
            user_purpose = typer.prompt("1. What is the main purpose/goal of this agent?")
            user_output_desc = typer.prompt(f"2. Describe the desired output structure. (Default is '{output_type}'. If complex, list fields and types. If simple text, type 'str')", default="str" if output_type.lower() == "str" else output_type)
            user_deps_desc = typer.prompt("3. Does the agent need external dependencies (e.g., database, API client)? If so, briefly describe them or type 'None'.", default="None")
            user_instructions_extra = typer.prompt("4. Any additional specific instructions or system prompt details for the agent?", default=system_prompt_instructions or "None")
            user_tools_desc = typer.prompt("5. Does the agent need specific tools? If so, list their names and a brief description of what they do, or type 'None'.", default="None")

            # Load the base template content to provide structure to the LLM
            base_template_path = generator.SDK_TEMPLATE_DIR / AGENT_TEMPLATE_SUBDIR / "agent_definition.py.j2"
            base_template_content = base_template_path.read_text()
            
            # Construct the prompt for the LLM
            ai_prompt = f"""
You are an expert Python developer specializing in Pydantic-AI. Your task is to generate the content for an 'agent_definition.py' file.
The generated code should be a fully functional Python module.
Ensure all necessary imports from pydantic_ai, pydantic, and typing are included.

Follow this base structure and instructions (from the template):
```python
{base_template_content}
```

Agent Name (to be used for class names like '{{{{ agent_name | capitalize }}}}Output'): {name}
LLM Configuration Name (to be used by `get_pydantic_ai_model` from `config.py`): {llm_config_name}

User requirements for the agent:
1. Main Purpose: {user_purpose}
2. Desired Output Structure ('str' if plain text, otherwise describe Pydantic model): {user_output_desc}
   (If not 'str', generate a Pydantic BaseModel class named '{output_type if output_type.lower() != 'str' else name.capitalize().replace('_','') + 'Output'}' for this.)
3. External Dependencies (describe or 'None'): {user_deps_desc}
   (If not 'None', generate a Pydantic BaseModel class named '{name.capitalize().replace('_','')}Deps' for this and set it as deps_type in Agent.)
4. Additional System Prompt Instructions (or 'None'): {user_instructions_extra if user_instructions_extra != "None" else (system_prompt_instructions or "Default instructions will be used.")}
5. Specific Tools (name and description, or 'None'): {user_tools_desc}
   (If tools are described, include placeholder function definitions for them, potentially in a commented-out section or by suggesting they go into 'tools.py' and be imported. For now, just define basic tool function signatures within agent_definition.py if simple, or note that they should be in tools.py)

Generation Instructions:
- Replace template placeholders like `{{{{ agent_name | capitalize }}}}Output` with actual class names based on the agent's name or user's output description.
- If `user_output_desc` is 'str', the `_output_type_actual` should be `str`. Otherwise, it should be the generated Pydantic class for the output.
- If `user_deps_desc` is not 'None', generate a Pydantic class for dependencies and set `_deps_type_actual` to this class. Otherwise, set it to `Any` or `None`.
- Populate the `Agent` initialization with the `configured_model` (loaded via `get_pydantic_ai_model`), the determined `_output_type_actual`, `_deps_type_actual`, and the system prompt.
- The system prompt should combine the base instruction "You are '{{agent_name}}', an AI assistant." with `agent_system_prompt_instructions` (from context) and `user_instructions_extra`.
- If tools are described, include their definitions or stubs. For example:
  ```python
  # from .tools import tool_one, tool_two # Assuming tools are in tools.py
  # agent.tools.extend([tool_one, tool_two])
  # OR, for simple tools defined directly:
  # @agent.tool
  # async def described_tool_one(ctx: RunContext[...], param1: str) -> str:
  #     \"\"\"User-described function for tool one.\"\"\"
  #     # TODO: Implement tool logic
  #     return "Result from tool_one"
  ```
- Ensure the final output is a single block of Python code for the `agent_definition.py` file. Do not include any explanatory text before or after the code block.
- The `settings.LLM_CONFIG_NAME` in the template refers to `{{{{ llm_config_name }}}}`.
- The `settings.LLM_MODEL_IDENTIFIER_FALLBACK` in the template refers to `{{{{ llm_model_identifier_fallback }}}}`.
- The `settings.AGENT_RETRIES` in the template refers to a default, you can set it to e.g. `1`.
- The `get_agent()` function should be present at the end.
- The `if __name__ == "__main__":` block should be present for direct testing of the definition file.

Generated Python code for agent_definition.py:
"""
            typer.echo("Generating 'agent_definition.py' content using AI. This may take a moment...")
            # print(f"DEBUG AI PROMPT:\n{ai_prompt}") # For debugging the prompt
            ai_generated_content = generation_agent.run_sync(ai_prompt).output
            
            # Basic cleanup: remove potential markdown code block fences
            if ai_generated_content.strip().startswith("```python"):
                ai_generated_content = ai_generated_content.strip()[9:]
            if ai_generated_content.strip().endswith("```"):
                ai_generated_content = ai_generated_content.strip()[:-3]
            
            agent_def_path = agent_module_path / "agent_definition.py"
            agent_def_path.write_text(ai_generated_content)
            typer.echo(f"AI-generated content written to '{agent_def_path.relative_to(Path.cwd())}'. Please review and customize.")

        except Exception as e:
            typer.echo(f"Error during AI-assisted generation: {e}", err=True)
            typer.echo("Falling back to standard template generation for 'agent_definition.py'.")
            # Fallback to standard template generation if AI fails
            generator.render_template(
                template_subdir=AGENT_TEMPLATE_SUBDIR,
                template_name="agent_definition.py.j2",
                output_path=agent_module_path / "agent_definition.py",
                context=context
            )
    else:
        # Standard template generation for agent_definition.py
        generator.render_template(
            template_subdir=AGENT_TEMPLATE_SUBDIR,
            template_name="agent_definition.py.j2",
            output_path=agent_module_path / "agent_definition.py",
            context=context
        )

    if agent_service_id in global_cfg.agents:
        typer.echo(f"Warning: Agent '{agent_service_id}' already exists in config. Skipping config update.", color=typer.colors.YELLOW)
    else:
        global_cfg.agents[agent_service_id] = config_manager.AgentServiceConfig(
            service_id=agent_service_id,
            llm_config_name=llm_config_name
        )
        config_manager.save_config(project_path, global_cfg)
        typer.echo(f"Agent '{name}' (service_id: '{agent_service_id}') added to '{config_file_path}'.")

    typer.echo(f"Agent '{name}' generated successfully in '{agent_module_path.relative_to(Path.cwd())}'.")
    typer.echo("Next steps:")
    typer.echo(f"1. Review and customize the agent files in '{agent_module_path.relative_to(Path.cwd())}'.")
    typer.echo(f"   - Especially 'agent_definition.py' for agent logic and 'tools.py' for custom tools.")
    if llm_config_name not in global_cfg.llms:
         typer.echo(f"2. IMPORTANT: LLM config '{llm_config_name}' is not yet defined in '{config_file_path}'.", color=typer.colors.RED)
         typer.echo(f"   Please define it using: 'alo-pyai-sdk config llm add --name {llm_config_name} ... --project-path {project_path_str}'", color=typer.colors.RED)
    else:
        typer.echo(f"2. LLM config '{llm_config_name}' will be used (defined in '{config_file_path}').")
    typer.echo(f"3. Run the agent service (after starting the registry): 'cd {project_path_str} && alo-pyai-sdk run agent {name}'")


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
    
    typer.echo(f"MCP client module '{name}' generated successfully at '{client_file_path.relative_to(Path.cwd())}'.")
    typer.echo("Next steps:")
    typer.echo(f"1. Review and customize the client module '{client_file_path.relative_to(Path.cwd())}'.")
    typer.echo(f"2. Import and use the `get_{client_module_name}_mcp_server()` factory in your agent's `mcp_servers` list or in `alo_config.yaml`.")

if __name__ == "__main__":
    app()
