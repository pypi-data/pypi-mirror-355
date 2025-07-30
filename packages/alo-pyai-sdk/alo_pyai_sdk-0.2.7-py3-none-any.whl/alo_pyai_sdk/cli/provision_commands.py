import typer
from typing import Optional
import subprocess

app = typer.Typer(
    name="provision",
    help="Provision cloud resources for your ALO PyAI project.",
    no_args_is_help=True,
)

db_app = typer.Typer(name="db", help="Provision database resources.", no_args_is_help=True)
app.add_typer(db_app, name="db")

def _run_gcloud_command(command_parts: list[str], step_description: str) -> bool:
    """Helper to run a gcloud command and print feedback."""
    typer.echo(f"\nAttempting to: {step_description}")
    full_command = " ".join(command_parts)
    typer.echo(f"Executing: {full_command}")
    
    # We will use subprocess here as execute_command tool is for the SDK's CLI,
    # not for running gcloud commands directly by the SDK user through the SDK.
    # However, for a real SDK, you'd want to use the execute_command tool
    # and get user approval for each step.
    # For this simulation, we'll just print and assume success/failure.
    
    # This is a placeholder for actual execution.
    # In a real scenario, you would use subprocess.run and handle output/errors.
    # For now, we'll simulate it.
    
    # Simulate asking for confirmation for critical steps
    if "create" in command_parts or "set-password" in command_parts:
        confirm = typer.confirm(f"Proceed with: {step_description}?", default=False)
        if not confirm:
            typer.echo("Operation cancelled by user.")
            return False
            
    typer.echo(f"(Placeholder) Simulating execution of: {full_command}")
    # try:
    #     process = subprocess.run(command_parts, capture_output=True, text=True, check=True)
    #     typer.echo("Command executed successfully.")
    #     if process.stdout:
    #         typer.echo("Output:\n" + process.stdout)
    #     return True
    # except subprocess.CalledProcessError as e:
    #     typer.echo(f"Error executing command: {e}", err=True)
    #     if e.stderr:
    #         typer.echo("Error Output:\n" + e.stderr, err=True)
    #     return False
    # except FileNotFoundError:
    #     typer.echo("Error: 'gcloud' command not found. Please ensure Google Cloud SDK is installed and in your PATH.", err=True)
    #     return False
    
    # Simulated success for now
    typer.echo(f"Successfully simulated: {step_description}")
    return True


@db_app.command("gcp-sql")
def provision_gcp_sql(
    project_id: Optional[str] = typer.Option(None, "--project-id", help="Google Cloud Project ID."),
    instance_name: str = typer.Option("dev-postgres", "--instance-name", help="Name for the Cloud SQL instance."),
    db_version: str = typer.Option("POSTGRES_15", "--db-version", help="PostgreSQL version (e.g., POSTGRES_15)."),
    cpu: int = typer.Option(1, "--cpu", help="Number of CPUs for the instance."),
    memory: str = typer.Option("3840MB", "--memory", help="Memory for the instance (e.g., 3840MB)."),
    region: str = typer.Option("europe-west1", "--region", help="Region for the instance."),
    storage_type: str = typer.Option("HDD", "--storage-type", help="Storage type (HDD or SSD)."),
    storage_size: int = typer.Option(10, "--storage-size", help="Storage size in GB."),
    no_auto_increase: bool = typer.Option(True, "--no-storage-auto-increase/--storage-auto-increase", help="Disable/enable storage auto increase."),
    postgres_password: Optional[str] = typer.Option(None, prompt=True, hide_input=True, confirmation_prompt=True, help="Password for the default 'postgres' user."),
    db_name: str = typer.Option("appdb", "--db-name", help="Name of the database to create within the instance."),
    app_user: str = typer.Option("appuser", "--app-user", help="Username for the new application user."),
    app_password: Optional[str] = typer.Option(None, prompt=True, hide_input=True, confirmation_prompt=True, help="Password for the new application user."),
):
    """
    Provisions a new PostgreSQL instance on Google Cloud SQL.
    """
    typer.echo("--- Google Cloud SQL PostgreSQL Provisioning ---")
    typer.echo("This command will guide you through provisioning a PostgreSQL instance.")
    typer.echo("Please ensure you have the Google Cloud SDK installed and configured (`gcloud auth login`).")

    if not project_id:
        project_id = typer.prompt("Enter your Google Cloud Project ID")

    typer.echo(f"\nUsing Project ID: {project_id}")
    typer.echo("Step 0: Ensure you are authenticated with gcloud and the project is set.")
    typer.echo(f"  Run: gcloud auth login")
    typer.echo(f"  Run: gcloud config set project {project_id}")
    if not typer.confirm("Have you authenticated with gcloud and set the project?", default=True):
        typer.echo("Please authenticate and set your project, then re-run this command.")
        raise typer.Exit()

    # 1. Create PostgreSQL instance
    cmd_create_instance = [
        "gcloud", "sql", "instances", "create", instance_name,
        f"--database-version={db_version}",
        f"--cpu={cpu}",
        f"--memory={memory}",
        f"--region={region}",
        f"--storage-type={storage_type}",
        f"--storage-size={storage_size}GB", # Add GB suffix
        "--no-storage-auto-increase" if no_auto_increase else "--storage-auto-increase",
        f"--project={project_id}",
    ]
    if not _run_gcloud_command(cmd_create_instance, f"Create PostgreSQL instance '{instance_name}'"):
        raise typer.Exit(code=1)

    # 2. Set password for 'postgres' user
    if not postgres_password: # Should have been prompted if None
        typer.echo("Error: Postgres password is required.", err=True)
        raise typer.Exit(code=1)
    cmd_set_pg_password = [
        "gcloud", "sql", "users", "set-password", "postgres",
        f"--instance={instance_name}",
        f"--password={postgres_password}",
        f"--project={project_id}",
    ]
    if not _run_gcloud_command(cmd_set_pg_password, "Set password for 'postgres' user"):
        raise typer.Exit(code=1)

    # 3. Create a database
    cmd_create_db = [
        "gcloud", "sql", "databases", "create", db_name,
        f"--instance={instance_name}",
        f"--project={project_id}",
    ]
    if not _run_gcloud_command(cmd_create_db, f"Create database '{db_name}'"):
        raise typer.Exit(code=1)

    # 4. Create a new custom user
    if not app_password: # Should have been prompted if None
        typer.echo("Error: Application user password is required.", err=True)
        raise typer.Exit(code=1)
    cmd_create_app_user = [
        "gcloud", "sql", "users", "create", app_user,
        f"--instance={instance_name}",
        f"--password={app_password}",
        f"--project={project_id}",
    ]
    if not _run_gcloud_command(cmd_create_app_user, f"Create application user '{app_user}'"):
        raise typer.Exit(code=1)

    typer.echo(f"\n--- Provisioning Summary for Instance '{instance_name}' ---")
    typer.echo(f"Instance Name: {instance_name}")
    typer.echo(f"Region: {region}")
    typer.echo(f"Database: {db_name}")
    typer.echo(f"Postgres User: postgres (password set)")
    typer.echo(f"Application User: {app_user} (password set)")
    typer.echo("You can typically connect to this instance using the Cloud SQL Proxy or by configuring public IP (not recommended for production without proper firewall rules).")
    typer.echo(f"To get connection name for proxy: gcloud sql instances describe {instance_name} --project={project_id} --format='value(connectionName)'")
    typer.echo("Provisioning complete (simulated).")

if __name__ == "__main__":
    app()
