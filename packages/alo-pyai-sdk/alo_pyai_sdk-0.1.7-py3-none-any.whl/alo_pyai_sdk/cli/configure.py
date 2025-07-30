import typer
from pathlib import Path
from typing import Optional, Dict, Any

from alo_pyai_sdk.core import config_manager

app = typer.Typer(
    name="config",
    help="Manage configurations for LLMs, MCP servers, etc.",
    no_args_is_help=True,
)

@app.command("llm")
def config_llm(
    action: str = typer.Argument(..., help="Action to perform: add, list, remove, update."),
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    name: Optional[str] = typer.Option(None, "--name", help="Name of the LLM configuration."),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (e.g., openai, anthropic, google-gla, groq, bedrock, mistral, cohere)."),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the LLM provider."),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="Default model name for this configuration (e.g., gpt-4o, claude-3-5-sonnet-latest)."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Optional base URL for self-hosted or compatible APIs."),
    extra_args_json: Optional[str] = typer.Option(None, "--extra-args", help="JSON string for provider-specific extra arguments (e.g., '{\"project_id\": \"my-gcp-project\"}')."),
):
    """
    Manage LLM configurations in the project's alo_config.yaml.
    """
    project_path = Path(project_path_str).resolve()
    config_file_path = config_manager.get_config_path(project_path)

    if not config_file_path.exists() and action != "init": # 'init' might be a future action to create a config
        typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
        typer.echo(f"Please run 'alo-pyai-sdk init {project_path_str}' or ensure you are in a project directory.")
        raise typer.Exit(code=1)

    if action == "add":
        if not name or not provider: # API key might be optional if using a local model or already in env
            typer.echo("Error: --name and --provider are required for 'add' action.", err=True)
            raise typer.Exit(code=1)
        
        try:
            cfg = config_manager.load_config(project_path)
            if name in cfg.llms:
                typer.echo(f"Error: LLM configuration named '{name}' already exists.", err=True)
                raise typer.Exit(code=1)

            import json
            parsed_extra_args: Optional[Dict[str, Any]] = None
            if extra_args_json:
                try:
                    parsed_extra_args = json.loads(extra_args_json)
                    if not isinstance(parsed_extra_args, dict):
                        typer.echo("Error: --extra-args must be a valid JSON object string.", err=True)
                        raise typer.Exit(code=1)
                except json.JSONDecodeError:
                    typer.echo("Error: Invalid JSON string provided for --extra-args.", err=True)
                    raise typer.Exit(code=1)

            new_llm_config = config_manager.LLMConfig(
                provider=provider,
                api_key=api_key, # Can be None if provider supports other auth or key is in env
                model_name=model_name,
                base_url=base_url,
                extra_args=parsed_extra_args
            )
            cfg.llms[name] = new_llm_config
            config_manager.save_config(project_path, cfg)
            typer.echo(f"LLM configuration '{name}' added successfully to '{config_file_path}'.")
            if not api_key:
                typer.echo(f"Warning: No API key provided for '{name}'. Ensure it's set in the environment if required by the provider.", color=typer.colors.YELLOW)

        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found. Cannot add LLM config.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error adding LLM configuration: {e}", err=True)
            raise typer.Exit(code=1)

    elif action == "list":
        try:
            cfg = config_manager.load_config(project_path)
            if not cfg.llms:
                typer.echo("No LLM configurations found.")
                return
            typer.echo("Available LLM configurations:")
            for llm_name, llm_conf in cfg.llms.items():
                details = f"  - {llm_name}: Provider={llm_conf.provider}, Model={llm_conf.model_name or 'Not set'}"
                if llm_conf.base_url:
                    details += f", BaseURL={llm_conf.base_url}"
                if llm_conf.api_key: # Just indicate if key is set, don't print it
                    details += ", APIKey=******"
                if llm_conf.extra_args:
                    details += f", ExtraArgs={llm_conf.extra_args}"
                typer.echo(details)
        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error listing LLM configurations: {e}", err=True)
            raise typer.Exit(code=1)
            
    elif action == "remove":
        if not name:
            typer.echo("Error: --name is required for 'remove' action.", err=True)
            raise typer.Exit(code=1)
        try:
            cfg = config_manager.load_config(project_path)
            if name not in cfg.llms:
                typer.echo(f"Error: LLM configuration named '{name}' not found.", err=True)
                raise typer.Exit(code=1)
            
            del cfg.llms[name]
            config_manager.save_config(project_path, cfg)
            typer.echo(f"LLM configuration '{name}' removed successfully from '{config_file_path}'.")
        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error removing LLM configuration: {e}", err=True)
            raise typer.Exit(code=1)

    elif action == "update":
        if not name:
            typer.echo("Error: --name is required for 'update' action.", err=True)
            raise typer.Exit(code=1)
        try:
            cfg = config_manager.load_config(project_path)
            if name not in cfg.llms:
                typer.echo(f"Error: LLM configuration named '{name}' not found.", err=True)
                raise typer.Exit(code=1)
            
            llm_to_update = cfg.llms[name]
            updated_fields = False
            if provider is not None:
                llm_to_update.provider = provider
                updated_fields = True
            if api_key is not None: # Allow explicitly setting api_key to empty string if desired
                llm_to_update.api_key = api_key
                updated_fields = True
            if model_name is not None:
                llm_to_update.model_name = model_name
                updated_fields = True
            if base_url is not None: # Allow explicitly setting base_url to empty string if desired
                llm_to_update.base_url = base_url if base_url else None # Store None if empty string
                updated_fields = True
            if extra_args_json is not None:
                import json
                try:
                    parsed_extra_args = json.loads(extra_args_json) if extra_args_json else None
                    if parsed_extra_args is not None and not isinstance(parsed_extra_args, dict):
                        typer.echo("Error: --extra-args must be a valid JSON object string or empty.", err=True)
                        raise typer.Exit(code=1)
                    llm_to_update.extra_args = parsed_extra_args
                    updated_fields = True
                except json.JSONDecodeError:
                    typer.echo("Error: Invalid JSON string provided for --extra-args.", err=True)
                    raise typer.Exit(code=1)
            
            if updated_fields:
                config_manager.save_config(project_path, cfg)
                typer.echo(f"LLM configuration '{name}' updated successfully in '{config_file_path}'.")
            else:
                typer.echo(f"No changes provided for LLM configuration '{name}'. Nothing updated.")

        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error updating LLM configuration: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        typer.echo(f"Error: Unknown action '{action}'. Must be one of 'add', 'list', 'remove', 'update'.", err=True)
        raise typer.Exit(code=1)


@app.command("mcp")
def config_mcp(
    action: str = typer.Argument(..., help="Action to perform: add, list, remove, update."),
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    name: Optional[str] = typer.Option(None, "--name", help="Name of the MCP server configuration."),
    url: Optional[str] = typer.Option(None, "--url", help="URL of the MCP server (for sse, streamable-http)."),
    transport_type: Optional[str] = typer.Option("sse", "--transport-type", "--type", help="Type of MCP server transport (stdio, sse, streamable-http)."),
    command: Optional[str] = typer.Option(None, "--command", help="Command to run for stdio MCP server."),
    args_str: Optional[str] = typer.Option(None, "--args", help="Comma-separated arguments for stdio command (e.g., 'run,main.py')."),
    tool_prefix: Optional[str] = typer.Option(None, "--tool-prefix", help="Prefix for tools from this MCP server."),
    # Add other common MCP parameters as needed
):
    """
    Manage MCP server configurations in the project's alo_config.yaml.
    """
    project_path = Path(project_path_str).resolve()
    config_file_path = config_manager.get_config_path(project_path)

    if not config_file_path.exists():
        typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
        typer.echo(f"Please run 'alo-pyai-sdk init {project_path_str}' or ensure you are in a project directory.")
        raise typer.Exit(code=1)

    if action == "add":
        if not name or not transport_type:
            typer.echo("Error: --name and --transport-type are required for 'add' action.", err=True)
            raise typer.Exit(code=1)
        
        if transport_type in ["sse", "streamable-http"] and not url:
            typer.echo(f"Error: --url is required for '{transport_type}' transport.", err=True)
            raise typer.Exit(code=1)
        if transport_type == "stdio" and not command:
            typer.echo("Error: --command is required for 'stdio' transport.", err=True)
            raise typer.Exit(code=1)

        try:
            cfg = config_manager.load_config(project_path)
            if name in cfg.mcp_servers:
                typer.echo(f"Error: MCP server configuration named '{name}' already exists.", err=True)
                raise typer.Exit(code=1)

            args_list: Optional[List[str]] = args_str.split(',') if args_str else None

            new_mcp_config = config_manager.MCPServerConfig(
                transport_type=transport_type,
                url=url,
                command=command,
                args=args_list,
                tool_prefix=tool_prefix
            )
            cfg.mcp_servers[name] = new_mcp_config
            config_manager.save_config(project_path, cfg)
            typer.echo(f"MCP server configuration '{name}' added successfully to '{config_file_path}'.")

        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found. Cannot add MCP server config.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error adding MCP server configuration: {e}", err=True)
            raise typer.Exit(code=1)

    elif action == "list":
        try:
            cfg = config_manager.load_config(project_path)
            if not cfg.mcp_servers:
                typer.echo("No MCP server configurations found.")
                return
            typer.echo("Available MCP server configurations:")
            for mcp_name, mcp_conf in cfg.mcp_servers.items():
                details = f"  - {mcp_name}: Type={mcp_conf.transport_type}"
                if mcp_conf.url:
                    details += f", URL={mcp_conf.url}"
                if mcp_conf.command:
                    details += f", Command='{mcp_conf.command}'"
                if mcp_conf.args:
                    details += f", Args={mcp_conf.args}"
                if mcp_conf.tool_prefix:
                    details += f", ToolPrefix='{mcp_conf.tool_prefix}'"
                typer.echo(details)
        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error listing MCP server configurations: {e}", err=True)
            raise typer.Exit(code=1)

    elif action == "remove":
        if not name:
            typer.echo("Error: --name is required for 'remove' action.", err=True)
            raise typer.Exit(code=1)
        try:
            cfg = config_manager.load_config(project_path)
            if name not in cfg.mcp_servers:
                typer.echo(f"Error: MCP server configuration named '{name}' not found.", err=True)
                raise typer.Exit(code=1)
            
            del cfg.mcp_servers[name]
            config_manager.save_config(project_path, cfg)
            typer.echo(f"MCP server configuration '{name}' removed successfully from '{config_file_path}'.")
        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error removing MCP server configuration: {e}", err=True)
            raise typer.Exit(code=1)

    elif action == "update":
        if not name:
            typer.echo("Error: --name is required for 'update' action.", err=True)
            raise typer.Exit(code=1)
        try:
            cfg = config_manager.load_config(project_path)
            if name not in cfg.mcp_servers:
                typer.echo(f"Error: MCP server configuration named '{name}' not found.", err=True)
                raise typer.Exit(code=1)

            mcp_to_update = cfg.mcp_servers[name]
            updated_fields = False

            if transport_type is not None:
                mcp_to_update.transport_type = transport_type
                updated_fields = True
            if url is not None: # Allow explicitly setting url to empty string if desired for some transports
                mcp_to_update.url = url if url else None
                updated_fields = True
            if command is not None: # Allow explicitly setting command to empty string if desired
                mcp_to_update.command = command if command else None
                updated_fields = True
            if args_str is not None:
                mcp_to_update.args = args_str.split(',') if args_str else None
                updated_fields = True
            if tool_prefix is not None: # Allow explicitly setting tool_prefix to empty string if desired
                mcp_to_update.tool_prefix = tool_prefix if tool_prefix else None
                updated_fields = True

            if updated_fields:
                config_manager.save_config(project_path, cfg)
                typer.echo(f"MCP server configuration '{name}' updated successfully in '{config_file_path}'.")
            else:
                typer.echo(f"No changes provided for MCP server configuration '{name}'. Nothing updated.")
        except FileNotFoundError:
             typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
             raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error updating MCP server configuration: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        typer.echo(f"Error: Unknown action '{action}'. Must be one of 'add', 'list', 'remove', 'update'.", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
