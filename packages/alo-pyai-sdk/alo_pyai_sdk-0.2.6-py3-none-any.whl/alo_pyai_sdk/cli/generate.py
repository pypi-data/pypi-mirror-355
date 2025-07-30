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
            from pydantic_ai import Agent as SdkAgent 
            
            sdk_llm_config_name = llm_config_name 
            
            generation_model_instance = _get_llm_for_generation(project_path, sdk_llm_config_name)
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
                llm_config_name_for_agent=llm_config_name,
                user_output_desc=user_output_desc,
                user_deps_desc=user_deps_desc,
                user_instructions_extra=user_instructions_extra,
                user_tools_desc=user_tools_desc,
                generated_output_type_name=output_type if output_type.lower() != "str" else f"{name.capitalize().replace('_','')}Output",
                generated_deps_type_name=f"{name.capitalize().replace('_','')}Deps" 
            )

            typer.echo("Generating 'agent_definition.py' content using AI. This may take a moment...")
            ai_generated_content = generation_agent.run_sync(ai_prompt).output
            
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
            generator.render_template(
                template_subdir=AGENT_TEMPLATE_SUBDIR,
                template_name="agent_definition.py.j2",
                output_path=agent_module_path / "agent_definition.py",
                context=context
            )
    else:
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
    typer.echo(f"3. Run the agent service (after starting the registry): 'cd {project_path_str} && python -m uvicorn agents.{agent_service_id}.main:app --port {actual_agent_port} --reload'")


def construct_ai_generation_prompt(
    agent_name: str,
    user_description: str, 
    llm_config_name_for_agent: str, 
    user_output_desc: str,
    user_deps_desc: str,
    user_instructions_extra: str,
    user_tools_desc: str,
    generated_output_type_name: str, 
    generated_deps_type_name: str    
) -> str:
    
    prompt = f'''You are an expert Python developer specialized in creating Pydantic-AI agents.
Your task is to generate ONLY the Python code content for an 'agent_definition.py' file.
Do NOT include any markdown fences (```python ... ```) or any explanatory text outside the Python code block.

The base 'agent_definition.py' template has been improved and now handles:
- Safe import of 'settings' from '.config' with fallbacks.
- Robust multi-step LLM configuration for 'configured_model' (trying get_pydantic_ai_model, then infer_model, then TestModel).
- Default '_output_type_actual = str'.
- Default '_deps_type_actual = Any'.
- Default 'tools=[]' in the Agent constructor.
- Loading of MCP servers.
- Necessary imports like Agent, RunContext, BaseModel, Field, Type, Any, Optional, List, Path, datetime, models, TestModel.

Your primary tasks are to define user-specific components based on the requirements below and integrate them correctly.

Agent Name: {agent_name}
User-provided Main Purpose/Goal: "{user_description}"
LLM Configuration Name for Agent (already handled by template): {llm_config_name_for_agent}

User Requirements & Your Actions:

IMPORTANT NOTE ON AGENT BEHAVIOR:
- If the agent's main purpose (described in `User-provided Main Purpose/Goal`) is direct content generation by the LLM (e.g., telling a story, answering a question, summarizing text based on its persona and system prompt), then the `tools` list passed to the `Agent` constructor should generally be EMPTY (`tools=[]`). This encourages the LLM to use its direct generation capabilities.
- If the user also describes specific, discrete actions that require external interaction or complex internal logic (e.g., "fetch current weather", "calculate mortgage payment", "search a database"), then these should be implemented as tools.
- Strive to create a powerful system prompt to guide direct generation when appropriate.

1.  Desired Output Structure: "{user_output_desc}"
    *   If '{user_output_desc.lower()}' is 'str', DO NOTHING for output type; the template defaults to `_output_type_actual = str`.
    *   Otherwise (if a custom structure is described):
        *   Define a Pydantic BaseModel class named '{generated_output_type_name}'.
        *   Assign this class to the `_output_type_actual` variable.
        *   Example:
            ```python
            # --- Define Agent Output Type ---
            class {generated_output_type_name}(BaseModel):
                story: str = Field(description="The generated story")
                characters: List[str] = Field(default_factory=list)
            _output_type_actual = {generated_output_type_name}
            ```

2.  External Dependencies: "{user_deps_desc}"
    *   If '{user_deps_desc.lower()}' is 'none' or empty, DO NOTHING for dependency type; the template defaults to `_deps_type_actual = Any`.
    *   Otherwise (if dependencies are described):
        *   Define a Pydantic BaseModel class named '{generated_deps_type_name}'.
        *   Assign this class to the `_deps_type_actual` variable.
        *   Example:
            ```python
            # --- Define Agent Dependencies Type ---
            class {generated_deps_type_name}(BaseModel):
                database_url: str
                api_key: Optional[str] = None
            _deps_type_actual = {generated_deps_type_name}
            ```

3.  Additional System Prompt Instructions: "{user_instructions_extra}"
    *   The template constructs `final_system_prompt` using `agent_name`, `user_description`, and this `agent_system_prompt_instructions` template variable: `{{{{ agent_system_prompt_instructions }}}}`.
    *   Your generated code should ensure the `agent_system_prompt_instructions` variable within the Jinja2 template context (which is `"{user_instructions_extra if user_instructions_extra.lower() != 'none' else ''}"`) is correctly used by the template.
    *   Essentially, the template already handles this: `system_prompt="""You are '{{{{ agent_name }}}}', an AI assistant. {{{{ agent_system_prompt_instructions | default("{user_description}") }}}}"""`.
    *   You just need to ensure your generated code doesn't interfere with this part of the template, or if you override `final_system_prompt`, do it correctly. The template's default system prompt is:
        `You are '{{{{agent_name}}}}', an AI assistant.\n    {{{{ agent_system_prompt_instructions | default("Please assist the user with their request.") }}}}`
        The `user_description` is already part of `agent_system_prompt_instructions` if `system_prompt_instructions` is not provided by the user.
        So, the `final_system_prompt` in the template should be sufficient. Do not redefine `final_system_prompt` unless absolutely necessary.

4.  Specific Tools: "{user_tools_desc}"
    *   If '{user_tools_desc.lower()}' is 'none' or empty, DO NOTHING for tools; the template defaults to `tools=[]`.
    *   Otherwise (if tools are described):
        *   Define each tool as a Python function (async or sync). Decorate it with `@agent.tool`.
        *   Include `RunContext` and appropriate type hints for parameters and return types.
        *   Collect all defined tool functions into a list.
        *   Modify the `agent = Agent(...)` call to include these tools: `tools=[tool_one_func, tool_two_func]`.
        *   Example:
            ```python
            # --- Define Tools ---
            # @agent.tool  <-- This decorator will be applied AFTER agent is defined.
            # async def get_weather(ctx: RunContext[_deps_type_actual], city: str) -> str:
            #     """Gets the current weather for a city."""
            #     # Actual implementation would go here
            #     return f"Weather in {{city}} is sunny."
            #
            # # In the Agent instantiation, you would pass the tool functions:
            # # agent = Agent(..., tools=[get_weather])
            # # The template initializes agent first, so you might need to append tools:
            # # if hasattr(get_weather, 'is_tool'): agent.tools.append(get_weather)
            # # Or, more simply, define tools before agent and pass them in the constructor.
            # # For AI generation, it's easier to define tools and then pass to constructor.
            
            # Correct approach for AI generation:
            # 1. Define tool functions.
            # 2. Create a list of these functions.
            # 3. Pass this list to the `tools` parameter in `Agent()` constructor.
            # Example of defining tools and then the agent:

            # async def tool_one_func(ctx: RunContext[Any], param: str) -> str: ...
            # agent_tools = [tool_one_func]
            # agent = Agent(
            #     ..., # other params
            #     tools=agent_tools
            # )
            ```
            The AI should define the tool functions if requested. If tools are defined, it should create a list of these functions (e.g., `my_tools = [tool_one_func, tool_two_func]`) and ensure this list is passed to the `tools` parameter of the `Agent` constructor.
    *   If the agent's main purpose is direct generation and no specific tool-like actions are described by the user (i.e., `user_tools_desc` is 'none' or empty), the AI should NOT define any tool functions or `agent_tools_list`. The template defaults to `tools=[]` in this case.

Structure of your generated Python code:
Your code will be injected into the `agent_definition.py.j2` template.
The template already includes necessary imports and robust LLM loading.
Focus on defining the Pydantic models for output/deps and tool functions if requested by the user.

Example of where your generated code fits:
```python
# [TEMPLATE IMPORTS AND FALLBACK SETTINGS - ALREADY PRESENT]
# [TEMPLATE ROBUST LLM CONFIGURATION FOR 'configured_model' - ALREADY PRESENT]

# --- Define Agent Output Type ---
# <<< YOUR CODE FOR OUTPUT MODEL DEFINITION AND ASSIGNMENT TO _output_type_actual GOES HERE (if not str) >>>
# Example:
# class {generated_output_type_name}(BaseModel): ...
# _output_type_actual = {generated_output_type_name}

# --- Define Agent Dependencies Type ---
# <<< YOUR CODE FOR DEPENDENCIES MODEL DEFINITION AND ASSIGNMENT TO _deps_type_actual GOES HERE (if not None) >>>
# Example:
# class {generated_deps_type_name}(BaseModel): ...
# _deps_type_actual = {generated_deps_type_name}

# [TEMPLATE MCP SERVER LOADING - ALREADY PRESENT]

# --- Define Tools (if any) ---
# <<< YOUR CODE FOR TOOL FUNCTION DEFINITIONS GOES HERE >>>
# Example:
# async def my_custom_tool(ctx: RunContext[Any], query: str) -> str:
#     return f"Processed: {{query}}"

# Create a list of tool functions if any were defined
# Example:
# agent_tools_list = [my_custom_tool] if "{user_tools_desc.lower()}" not in ["none", ""] else []
agent_tools_list = [] # Initialize empty, AI to populate if tools are defined
# <<< IF TOOLS ARE DEFINED, POPULATE agent_tools_list HERE >>>


# [TEMPLATE Agent INSTANTIATION - MODIFIED TO USE agent_tools_list]
# The template will look like:
# agent = Agent(
#     model=configured_model,
#     output_type=_output_type_actual,
#     deps_type=_deps_type_actual,
#     system_prompt=..., # Handled by template
#     mcp_servers=mcp_servers_list, # Handled by template
#     tools=agent_tools_list, # <--- YOUR LIST OF TOOLS
#     retries=settings.AGENT_RETRIES
# )

# [TEMPLATE get_agent() FUNCTION AND __main__ BLOCK - ALREADY PRESENT]
```

Ensure your output is ONLY the Python code. Do not add comments like "<<< YOUR CODE ... >>>".
The AI should generate the necessary Python code for:
1. Defining `{generated_output_type_name}` and assigning to `_output_type_actual` IF `user_output_desc` is not 'str'.
2. Defining `{generated_deps_type_name}` and assigning to `_deps_type_actual` IF `user_deps_desc` is not 'None'.
3. Defining tool functions and creating `agent_tools_list` IF `user_tools_desc` is not 'None'.
The rest of the `agent_definition.py` structure is provided by the template.
The `agent` object will be decorated with tools AFTER its instantiation if tools are defined inline with `@agent.tool`.
For AI generation, the preferred method is:
1. Define tool functions.
2. Create a list of these functions (e.g., `agent_tools_list = [tool_one, tool_two]`).
3. The `agent_definition.py.j2` template is now structured to correctly use this `agent_tools_list` if it's defined by your generated code, or default to `tools=[]` if `agent_tools_list` is not defined.
   Your generated code should ONLY define `agent_tools_list` if tools are actually created based on user input.
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
            # I parametri type, url, command, args, tool_prefix sono usati per generare il client,
            # ma potrebbero anche essere memorizzati qui per riferimento o per usi futuri
            # se la factory function li accettasse come override.
            # Per ora, li omettiamo dalla configurazione salvata se module/factory sono presenti,
            # poiché la factory generata li avrà hardcoded o li prenderà da env var.
            # Se si volesse una configurazione più flessibile, la factory dovrebbe accettarli.
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
