from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader

# Assuming templates are within the SDK's 'templates' directory
SDK_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

def render_template(
    template_subdir: str, # e.g., "fastapi_agent" or "fastapi_registry"
    template_name: str,   # e.g., "main.py.j2"
    output_path: Path,
    context: Dict[str, Any],
) -> None:
    """
    Renders a Jinja2 template and writes it to the specified output path.

    Args:
        template_subdir: The subdirectory within the SDK's templates folder
                         where the template file is located.
        template_name: The name of the template file (including .j2 extension).
        output_path: The full path where the rendered file should be saved.
        context: A dictionary of variables to pass to the template.
    """
    env = Environment(
        loader=FileSystemLoader(SDK_TEMPLATE_DIR / template_subdir),
        autoescape=False, # Typically false for code generation
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    template = env.get_template(template_name)
    rendered_content = template.render(context)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rendered_content)
    print(f"Generated: {output_path.relative_to(Path.cwd())}")


def generate_project_structure(
    project_path: Path,
    template_subdir: str,
    structure: Dict[str, str], # Maps output relative path to template name
    context: Dict[str, Any],
) -> None:
    """
    Generates a directory structure based on templates.

    Args:
        project_path: The root path of the project where files will be generated.
        template_subdir: The subdirectory within SDK templates for these files.
        structure: A dictionary where keys are relative output file paths
                   (e.g., "main.py", "core/models.py") and values are the
                   corresponding template names (e.g., "main.py.j2").
        context: The context to pass to all templates.
    """
    for output_rel_path, template_file_name in structure.items():
        output_full_path = project_path / output_rel_path
        render_template(
            template_subdir=template_subdir,
            template_name=template_file_name,
            output_path=output_full_path,
            context=context,
        )

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    example_project_dir = Path(".") / "temp_alo_project_generated"
    example_project_dir.mkdir(exist_ok=True)

    # Simulate generating a simple file
    SDK_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True) # Ensure base template dir exists
    (SDK_TEMPLATE_DIR / "test_module").mkdir(exist_ok=True)
    with open(SDK_TEMPLATE_DIR / "test_module" / "test.txt.j2", "w") as f:
        f.write("Hello, {{ name }}!")

    render_template(
        template_subdir="test_module",
        template_name="test.txt.j2",
        output_path=example_project_dir / "greeting.txt",
        context={"name": "ALO PyAI User"}
    )

    # Simulate generating a structure
    (SDK_TEMPLATE_DIR / "another_module").mkdir(exist_ok=True)
    with open(SDK_TEMPLATE_DIR / "another_module" / "app.py.j2", "w") as f:
        f.write("from fastapi import FastAPI\n\napp = FastAPI(title='{{ project_title }}')")
    with open(SDK_TEMPLATE_DIR / "another_module" / "config.py.j2", "w") as f:
        f.write("API_VERSION = '{{ version }}'")
    
    generate_project_structure(
        project_path=example_project_dir / "my_app",
        template_subdir="another_module",
        structure={
            "main.py": "app.py.j2",
            "core/settings.py": "config.py.j2"
        },
        context={"project_title": "My Awesome App", "version": "1.0"}
    )

    print(f"\nCheck generated files in: {example_project_dir.resolve()}")
    # To clean up:
    # import shutil
    # shutil.rmtree(example_project_dir)
    # shutil.rmtree(SDK_TEMPLATE_DIR / "test_module")
    # shutil.rmtree(SDK_TEMPLATE_DIR / "another_module")
