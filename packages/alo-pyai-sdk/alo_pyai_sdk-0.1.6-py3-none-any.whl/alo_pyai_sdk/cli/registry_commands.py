import typer
from pathlib import Path
from typing import Optional
import httpx # Added for RegistryClient

from alo_pyai_sdk.core import config_manager
from alo_pyai_sdk.core import registry_client

app = typer.Typer(
    name="registry",
    help="Manage and interact with the Agent Registry.",
    no_args_is_help=True,
)

@app.command("list-agents")
def list_agents(
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
):
    """
    Lists all agents currently registered with the Agent Registry defined in the project's config.
    """
    project_path = Path(project_path_str).resolve()
    config_file_path = config_manager.get_config_path(project_path)

    if not config_file_path.exists():
        typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
        typer.echo(f"Please run 'alo-pyai-sdk init {project_path_str}' or ensure you are in a project directory.")
        raise typer.Exit(code=1)

    try:
        cfg = config_manager.load_config(project_path)
        registry_base_url = f"http://{cfg.registry.host}:{cfg.registry.port}"
        client = registry_client.RegistryClient(registry_base_url)
        
        typer.echo(f"Fetching registered agents from {registry_base_url}...")
        agents = client.list_agents()
        
        if not agents:
            typer.echo("No agents found or registry not responding.")
            return
            
        typer.echo("Registered Agents:")
        for agent_id, agent_info in agents.items():
            details = f"  - ID: {agent_id}"
            if agent_info.name:
                details += f", Name: {agent_info.name}"
            if agent_info.service_url:
                details += f", URL: {agent_info.service_url}"
            if agent_info.description:
                details += f", Description: '{agent_info.description}'"
            if agent_info.skills:
                details += f", Skills: {', '.join(agent_info.skills)}"
            typer.echo(details)
            
    except httpx.RequestError as e:
        typer.echo(f"Error connecting to the Agent Registry at {registry_base_url}: {e}", err=True)
        typer.echo("Please ensure the Agent Registry server is running.")
    except FileNotFoundError:
        typer.echo(f"Error: Project config file '{config_file_path}' not found.", err=True)
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)


@app.command("run")
def run_registry(
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Override the port defined in alo_config.yaml for the registry."),
    host: Optional[str] = typer.Option(None, "--host", help="Override the host defined in alo_config.yaml for the registry."),
):
    """
    Guides on how to run the Agent Registry FastAPI application for the current project.
    The actual execution should be done from within the project's 'agent_registry' directory.
    """
    project_path = Path(project_path_str).resolve()
    config_file_path = config_manager.get_config_path(project_path)
    registry_app_dir = project_path / "agent_registry"

    if not config_file_path.exists() or not registry_app_dir.exists():
        typer.echo(f"Error: Project not initialized correctly or 'agent_registry' directory not found in '{project_path}'.", err=True)
        typer.echo(f"Please run 'alo-pyai-sdk init {project_path_str}' first.")
        raise typer.Exit(code=1)
        
    try:
        cfg = config_manager.load_config(project_path)
        actual_port = port if port is not None else cfg.registry.port
        actual_host = host if host is not None else cfg.registry.host
        
        typer.echo(f"To run the Agent Registry for project '{project_path.name}':")
        typer.echo(f"1. Navigate to the registry directory: cd {registry_app_dir.relative_to(Path.cwd())}")
        typer.echo(f"2. Run the FastAPI application, for example using uvicorn:")
        typer.echo(f"   uvicorn main:app --host {actual_host} --port {actual_port} --reload")
        typer.echo("\nNote: This SDK command provides guidance. You need to run the uvicorn command manually from the 'agent_registry' directory.")

    except Exception as e:
        typer.echo(f"Error reading project configuration: {e}", err=True)


if __name__ == "__main__":
    app()
