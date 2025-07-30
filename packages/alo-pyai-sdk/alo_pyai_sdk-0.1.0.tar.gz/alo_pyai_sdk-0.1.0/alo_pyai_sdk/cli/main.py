import typer

app = typer.Typer(
    name="alo-pyai-sdk",
    help="SDK to facilitate the creation of AI agentic applications.",
    no_args_is_help=True,
)

@app.command()
def version():
    """
    Show the version of the ALO PyAI SDK.
    """
    # This will be replaced with dynamic versioning later
    from alo_pyai_sdk import __version__ as sdk_version # Placeholder for actual version import
    typer.echo(f"ALO PyAI SDK Version: {sdk_version}")

from . import generate
from . import configure
from . import registry_commands

app.add_typer(generate.app, name="generate")
app.add_typer(configure.app, name="config")
app.add_typer(registry_commands.app, name="registry")

if __name__ == "__main__":
    app()
