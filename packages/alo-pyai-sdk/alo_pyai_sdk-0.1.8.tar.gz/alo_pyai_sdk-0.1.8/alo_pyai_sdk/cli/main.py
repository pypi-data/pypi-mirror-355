import typer
from pathlib import Path
import shutil
from typing import Optional # Import Optional

from alo_pyai_sdk.core import generator, config_manager
from alo_pyai_sdk import __version__ as sdk_version # Import at module level

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
    typer.echo(f"ALO PyAI SDK Version: {sdk_version}")

REGISTRY_TEMPLATE_SUBDIR = "fastapi_registry"
REGISTRY_FILES_STRUCTURE = {
    "main.py": "main.py.j2",
    "models.py": "models.py.j2",
    "config.py": "config.py.j2",
    "__init__.py": "__init__.py.j2",
}

@app.command()
def init(
    project_name: str = typer.Argument(..., help="The name of the new project. A directory with this name will be created."),
    path_str: Optional[str] = typer.Option(None, "--path", help="Optional path where the project directory should be created. Defaults to current directory.")
):
    """
    Initializes a new ALO PyAI project with an Agent Registry.
    Creates a project directory, an 'alo_config.yaml', and a FastAPI app for the registry.
    """
    if path_str:
        base_path = Path(path_str).resolve()
        if not base_path.is_dir():
            typer.echo(f"Error: Provided path '{base_path}' is not a valid directory.", err=True)
            raise typer.Exit(code=1)
    else:
        base_path = Path(".").resolve()

    project_path = base_path / project_name.lower().replace(" ", "_").replace("-", "_")

    if project_path.exists():
        typer.echo(f"Error: Project directory '{project_path}' already exists.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Initializing new ALO PyAI project '{project_name}' at '{project_path}'...")
    
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create initial alo_config.yaml
        initial_config = config_manager.GlobalConfig(
            registry=config_manager.RegistryConfig(host="0.0.0.0", port=8000) # Default registry config
        )
        config_manager.save_config(project_path, initial_config)
        typer.echo(f"Created global configuration: {config_manager.get_config_path(project_path).relative_to(Path.cwd())}")

        # Scaffold the Agent Registry app
        registry_app_path = project_path / "agent_registry"
        registry_app_path.mkdir(parents=True, exist_ok=True)
        
        context = {
            "project_name": project_name,
            "sdk_version": sdk_version, # Use the SDK's version
            "registry_port": initial_config.registry.port
        }
        generator.generate_project_structure(
            project_path=registry_app_path,
            template_subdir=REGISTRY_TEMPLATE_SUBDIR,
            structure=REGISTRY_FILES_STRUCTURE,
            context=context,
        )
        typer.echo(f"Agent Registry application scaffolded in '{registry_app_path.relative_to(Path.cwd())}'.")
        
        # Create .gitignore
        gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# PEP 582; __pypackages__
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype
.pytype/

# Cython debug symbols
cython_debug/

# VSCode
.vscode/

# Temp files
*.tmp
*.bak
*.swp
*~
"""
        with open(project_path / ".gitignore", "w") as f:
            f.write(gitignore_content)
        typer.echo(f"Created .gitignore file.")

        typer.echo(f"\nProject '{project_name}' initialized successfully!")
        typer.echo("Next steps:")
        typer.echo(f"1. cd {project_path.relative_to(Path.cwd())}")
        typer.echo("2. Configure your LLMs: 'alo-pyai-sdk config llm add ...'")
        typer.echo("3. Generate your first agent: 'alo-pyai-sdk generate agent YourAgentName'")
        typer.echo("4. Start the registry: 'alo-pyai-sdk run registry'")

    except Exception as e:
        typer.echo(f"Error during project initialization: {e}", err=True)
        # Attempt to clean up created directory if initialization failed
        if project_path.exists():
            typer.echo(f"Cleaning up '{project_path}' due to error...", color=typer.colors.YELLOW)
            shutil.rmtree(project_path)
        raise typer.Exit(code=1)


from . import generate
from . import configure
from . import registry_commands
from . import run_commands
from . import provision_commands

app.add_typer(generate.app, name="generate")
app.add_typer(configure.app, name="config")
app.add_typer(registry_commands.app, name="registry")
app.add_typer(run_commands.app, name="run")
app.add_typer(provision_commands.app, name="provision")

if __name__ == "__main__":
    app()
