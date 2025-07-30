import typer
from pathlib import Path
from typing import Optional, List, Any, Dict

from alo_pyai_sdk.core import generator
from alo_pyai_sdk.core import config_manager
from pydantic_ai import models # Aggiunto import

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
    llm_config_name: str = typer.Option("mana_llm", "--llm-config", "-l", help="Name of the LLM configuration to use (from alo_config.yaml) for the agent itself AND for AI-assisted generation if used."),
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
        "llm_config_name": llm_config_name, # Used by settings in config.py.j2
        "llm_model_identifier_fallback": "openai:gpt-4o", # Used by settings
        "agent_output_type": output_type if output_type.lower() != "str" else f"{name.capitalize().replace('_','')}Output", # For AI prompt
        "agent_output_type_is_str": output_type.lower() == "str", # For agent_definition.py.j2 logic
        "agent_deps_type": "Any", # For AI prompt
        "agent_system_prompt_instructions": system_prompt_instructions or f"You are {name}, an AI assistant. Please assist the user.", # For agent_definition.py.j2
        "agent_retries": 1 # Default, used by settings in config.py.j2
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
            from pydantic_ai import Agent as SdkAgent 
            
            sdk_llm_config_name_for_gen = llm_config_name # Use the same LLM config for generation
            
            generation_model_instance = _get_llm_for_generation(project_path, sdk_llm_config_name_for_gen)
            generation_agent = SdkAgent(model=generation_model_instance, output_type=str)

            typer.echo("Please describe the agent's functionalities:")
            user_purpose = typer.prompt("1. What is the main purpose/goal of this agent?")
            user_output_desc = typer.prompt(f"2. Describe the desired output structure. (Default is '{output_type}'. If complex, list fields and types. If simple text, type 'str')", default="str" if output_type.lower() == "str" else output_type)
            user_deps_desc = typer.prompt("3. Does the agent need external dependencies (e.g., database, API client)? If so, briefly describe them or type 'None'.", default="None")
            user_instructions_extra = typer.prompt("4. Any additional specific instructions or system prompt details for the agent?", default=system_prompt_instructions or "None")
            user_tools_desc = typer.prompt("5. Does the agent need specific tools? If so, list their names and a brief description of what they do, or type 'None'.", default="None")
            
            ai_prompt = construct_ai_generation_prompt(
                agent_name=name,
                user_description=user_purpose,
                user_output_desc=user_output_desc,
                user_deps_desc=user_deps_desc,
                user_instructions_extra=user_instructions_extra,
                user_tools_desc=user_tools_desc,
                # These are for naming the classes if AI defines them
                generated_output_type_name=context["agent_output_type"], 
                generated_deps_type_name=f"{name.capitalize().replace('_','')}Deps"
            )

            typer.echo("Generating 'agent_definition.py' content using AI. This may take a moment...")
            ai_generated_content = generation_agent.run_sync(ai_prompt).output
            
            # Clean up potential markdown fences from AI output
            if ai_generated_content.strip().startswith("```python"):
                ai_generated_content = ai_generated_content.strip()[9:]
            if ai_generated_content.strip().endswith("```"):
                ai_generated_content = ai_generated_content.strip()[:-3]
            
            agent_def_path = agent_module_path / "agent_definition.py"
            # The AI generates the *full* content for agent_definition.py now
            agent_def_path.write_text(ai_generated_content) 
            typer.echo(f"AI-generated content written to '{agent_def_path.relative_to(Path.cwd())}'. Please review and customize.")

        except Exception as e:
            typer.echo(f"Error during AI-assisted generation: {e}", err=True)
            typer.echo("Falling back to standard template generation for 'agent_definition.py'.")
            # Render the base template if AI fails
            generator.render_template(
                template_subdir=AGENT_TEMPLATE_SUBDIR,
                template_name="agent_definition.py.j2", # The base template
                output_path=agent_module_path / "agent_definition.py",
                context=context
            )
    else:
        # Standard template generation if not AI-assisted
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
            llm_config_name=llm_config_name # This is the LLM config the agent *should* use
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
    typer.echo(f"3. Run the agent service (after starting the registry): 'cd {project_path_str} && python -m uvicorn agents.{agent_service_id}.main:app --port {actual_agent_port} --reload'")


def construct_ai_generation_prompt(
    agent_name: str,
    user_description: str, 
    user_output_desc: str,
    user_deps_desc: str,
    user_instructions_extra: str,
    user_tools_desc: str,
    generated_output_type_name: str, 
    generated_deps_type_name: str    
) -> str:
    
    prompt = f'''You are an expert Python developer specialized in creating Pydantic-AI agents.
Your task is to generate the COMPLETE Python code content for an 'agent_definition.py' file.
The generated code should be a fully functional Python module.
Do NOT include any markdown fences (```python ... ```) or any explanatory text outside the Python code block.

The 'agent_definition.py' file should generally follow this structure:
1.  Imports: `pydantic_ai.Agent`, `RunContext`, `models`, specific model/provider classes (e.g., `OpenAIModel`, `OpenAIProvider`), `BaseModel`, `Field`, `Type`, `Any`, `Optional`, `List`, `Path`, `yaml`.
2.  Attempt to import `settings` from `.config`. Include a `FallbackAgentSettings` class if the import fails.
3.  LLM Configuration Section:
    *   Initialize `configured_model = None`.
    *   Get `llm_config_name_to_load` from `settings.LLM_CONFIG_NAME`.
    *   Determine `alo_config_path` (e.g., `Path(__file__).resolve().parent.parent.parent / "alo_config.yaml"`).
    *   Try to open and parse `alo_config.yaml` using `yaml.safe_load()`.
    *   If the config for `llm_config_name_to_load` is found:
        *   Implement logic for the 'openai' provider: extract api_key, model_name, base_url; instantiate `OpenAIProvider` and `OpenAIModel`.
        *   (Optional) Add placeholder comments for other providers like 'anthropic', etc.
    *   If direct loading fails or provider not 'openai', fall back to `models.infer_model(settings.LLM_MODEL_IDENTIFIER_FALLBACK)`.
    *   If all above fail, fall back to `TestModel` from `pydantic_ai.models.test`.
    *   Include extensive print statements for debugging throughout this section.
4.  Define Agent Output Type:
    *   If `user_output_desc` is 'str', set `_output_type_actual: Type[Any] = str`.
    *   Otherwise, define a Pydantic `BaseModel` class named `{generated_output_type_name}` based on `user_output_desc` and assign it to `_output_type_actual`.
5.  Define Agent Dependencies Type:
    *   If `user_deps_desc` is 'none' or empty, set `_deps_type_actual: Type[Any] = Any`.
    *   Otherwise, define a Pydantic `BaseModel` class named `{generated_deps_type_name}` based on `user_deps_desc` and assign it to `_deps_type_actual`.
6.  MCP Server Loading:
    *   Initialize `mcp_servers_list: List[MCPServer] = []`.
    *   Attempt to import `load_mcp_servers_from_project_config` from `alo_pyai_sdk.core.llm_loader`.
    *   Call it using the project root path.
7.  Define Tool Functions (if `user_tools_desc` is not 'none' or empty):
    *   Define each tool as a Python function (async or sync) with `RunContext` and type hints.
    *   These functions should NOT be decorated with `@agent.tool` at this stage.
8.  Create `agent_tools_list`:
    *   If tools were defined in step 7, create a list containing these tool functions (e.g., `agent_tools_list = [my_tool_one, my_tool_two]`).
    *   If no tools were defined (or if the agent's main purpose is direct generation and `user_tools_desc` was 'none'), initialize `agent_tools_list = []`.
9.  Construct System Prompt:
    *   Create `final_system_prompt` using `agent_name`, `user_description`, and `user_instructions_extra`.
10. Create Agent Instance:
    *   Instantiate the `Agent` class, passing `configured_model`, `_output_type_actual`, `_deps_type_actual`, `final_system_prompt`, `mcp_servers_list`, and `agent_tools_list` (which will be empty if no tools).
    *   Use `settings.AGENT_RETRIES`.
11. Define `get_agent()` function.
12. Include an `if __name__ == "__main__":` block for basic testing and printing of agent configuration.

Agent Name: {agent_name}
User-provided Main Purpose/Goal: "{user_description}"
User-provided Desired Output Structure: "{user_output_desc}" (Name for class: {generated_output_type_name})
User-provided External Dependencies: "{user_deps_desc}" (Name for class: {generated_deps_type_name})
User-provided Additional System Prompt Instructions: "{user_instructions_extra}"
User-provided Specific Tools: "{user_tools_desc}"

IMPORTANT GUIDANCE:
- Direct Generation vs. Tools: If the agent's main purpose is direct content generation (e.g., storytelling), ensure `agent_tools_list` is `[]`. If specific actions are described as tools, implement them.
- System Prompt: Craft a powerful `final_system_prompt` to guide direct LLM responses.
- Imports: Ensure all necessary modules are imported at the top of the file.
- Robustness: Follow the multi-layer fallback for LLM configuration.

Your output should be ONLY the complete Python code for the 'agent_definition.py' file.
'''
    return prompt

def _get_llm_for_generation(project_path: Path, llm_config_name_for_gen: Optional[str]) -> models.Model:
    from alo_pyai_sdk.core.llm_loader import get_pydantic_ai_model as get_sdk_llm_internal
    # models è già importato a livello di modulo

    global_cfg = config_manager.load_config(project_path)
    
    if llm_config_name_for_gen and llm_config_name_for_gen in global_cfg.llms:
        return get_sdk_llm_internal(llm_config_name_for_gen, project_path)
    elif "mana_llm" in global_cfg.llms: # Check for mana_llm first
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found for AI generation. Falling back to 'mana_llm'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal("mana_llm", project_path)
    elif "default_openai" in global_cfg.llms: # Then check for default_openai
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found for AI generation. Falling back to 'default_openai'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal("default_openai", project_path)
    elif global_cfg.llms: # Then any other available
        first_config_name = list(global_cfg.llms.keys())[0]
        typer.echo(f"Warning: LLM config '{llm_config_name_for_gen}' not found for AI generation. Falling back to '{first_config_name}'.", color=typer.colors.YELLOW)
        return get_sdk_llm_internal(first_config_name, project_path)
    else:
        typer.echo(f"Error: No LLM configurations found. Cannot use AI-assisted generation.", err=True)
        typer.echo("Attempting to use 'openai:gpt-4o' as a last resort for generation, ensure OPENAI_API_KEY is set.", color=typer.colors.YELLOW)
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

    # Add the generated client to alo_config.yaml
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
