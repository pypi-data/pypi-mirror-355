import typer
from pathlib import Path
from typing import Optional

from alo_pyai_sdk.core import config_manager

app = typer.Typer(
    name="run",
    help="Run components of your ALO PyAI project (e.g., agent registry, specific agents).",
    no_args_is_help=True,
)

@app.command("registry")
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

@app.command("agent")
def run_agent(
    agent_name: str = typer.Argument(..., help="The service_id of the agent to run (as defined in alo_config.yaml)."),
    project_path_str: str = typer.Option(".", "--project-path", "-pp", help="The root path of the ALO PyAI project. Defaults to current directory."),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Override the agent's default port (from its own config.py or dynamically assigned)."),
    host: Optional[str] = typer.Option(None, "--host", help="Override the agent's default host (0.0.0.0)."),
):
    """
    Guides on how to run a specific Agent service for the current project.
    The actual execution should be done from within the agent's specific directory.
    """
    project_path = Path(project_path_str).resolve()
    agent_service_id = agent_name.lower().replace(" ", "_").replace("-", "_")
    agent_app_dir = project_path / "agents" / agent_service_id

    if not agent_app_dir.exists() or not (agent_app_dir / "main.py").exists():
        typer.echo(f"Error: Agent service '{agent_name}' (directory: '{agent_service_id}') not found or 'main.py' is missing in '{agent_app_dir}'.", err=True)
        typer.echo(f"Please ensure the agent has been generated correctly using 'alo-pyai-sdk generate agent {agent_name}'.")
        raise typer.Exit(code=1)
        
    # Note: The actual port for an agent is defined in its own config.py (generated from template).
    # This command primarily provides guidance. Overriding here is for convenience in the guidance message.
    # A more advanced version could try to read the agent's specific config.py.
    
    actual_host = host if host is not None else "0.0.0.0"
    port_guidance = f"--port {port}" if port is not None else "(uses port from agent's config.py, typically 8001 or as specified during generation)"

    typer.echo(f"To run the Agent service '{agent_name}':")
    typer.echo(f"1. Navigate to the agent's directory: cd {agent_app_dir.relative_to(Path.cwd())}")
    typer.echo(f"2. Run the FastAPI application, for example using uvicorn:")
    typer.echo(f"   uvicorn main:app --host {actual_host} {port_guidance} --reload")
    typer.echo(f"\nNote: Ensure the Agent Registry is running and accessible by this agent (check agent's config.py and registry URL).")

if __name__ == "__main__":
    app()
