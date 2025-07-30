import re
from pathlib import Path

import typer
from rich.console import Console

# Setup rich console and logging
console = Console()

app = typer.Typer(name="codegen")


@app.command()
def generate(
    schema_path: Path = typer.Option(..., "--schema", "-s"),
    output_path: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path - should match the API name (e.g., 'twitter.py' for Twitter API)",
    ),
    class_name: str = typer.Option(
        None,
        "--class-name",
        "-c",
        help="Class name to use for the API client",
    ),
):
    """Generate API client from OpenAPI schema with optional docstring generation.

    The output filename should match the name of the API in the schema (e.g., 'twitter.py' for Twitter API).
    This name will be used for the folder in applications/.
    """
    # Import here to avoid circular imports
    from universal_mcp.utils.openapi.api_generator import generate_api_from_schema

    if not schema_path.exists():
        console.print(f"[red]Error: Schema file {schema_path} does not exist[/red]")
        raise typer.Exit(1)

    try:
        app_file_data = generate_api_from_schema(
            schema_path=schema_path,
            output_path=output_path,
            class_name=class_name,
        )
        if isinstance(app_file_data, dict) and "code" in app_file_data:
            console.print("[yellow]No output path specified, printing generated code to console:[/yellow]")
            console.print(app_file_data["code"])
        elif isinstance(app_file_data, Path):
            console.print("[green]API client successfully generated and installed.[/green]")
            console.print(f"[blue]Application file: {app_file_data}[/blue]")
        else:
            # Handle the error case from api_generator if validation fails
            if isinstance(app_file_data, dict) and "error" in app_file_data:
                console.print(f"[red]{app_file_data['error']}[/red]")
                raise typer.Exit(1)
            else:
                console.print("[red]Unexpected return value from API generator.[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error generating API client: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def readme(
    file_path: Path = typer.Argument(..., help="Path to the Python file to process"),
):
    """Generate a README.md file for the API client."""
    from universal_mcp.utils.openapi.readme import generate_readme

    readme_file = generate_readme(file_path)
    console.print(f"[green]README.md file generated at: {readme_file}[/green]")


@app.command()
def docgen(
    file_path: Path = typer.Argument(..., help="Path to the Python file to process"),
    model: str = typer.Option(
        "perplexity/sonar",
        "--model",
        "-m",
        help="Model to use for generating docstrings",
    ),
):
    """Generate docstrings for Python files using LLMs.

    This command uses litellm with structured output to generate high-quality
    Google-style docstrings for all functions in the specified Python file.
    """
    from universal_mcp.utils.openapi.docgen import process_file

    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    try:
        processed = process_file(str(file_path), model)
        console.print(f"[green]Successfully processed {processed} functions[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def init(
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for the project (must exist)",
    ),
    app_name: str | None = typer.Option(
        None,
        "--app-name",
        "-a",
        help="App name (letters, numbers, hyphens, underscores only)",
    ),
    integration_type: str | None = typer.Option(
        None,
        "--integration-type",
        "-i",
        help="Integration type (api_key, oauth, agentr, none)",
        case_sensitive=False,
        show_choices=True,
    ),
):
    """Initialize a new MCP project using the cookiecutter template."""
    from cookiecutter.main import cookiecutter

    NAME_PATTERN = r"^[a-zA-Z0-9_-]+$"

    def validate_pattern(value: str, field_name: str) -> None:
        if not re.match(NAME_PATTERN, value):
            console.print(
                f"[red]❌ Invalid {field_name}; only letters, numbers, hyphens, and underscores allowed.[/red]"
            )
            raise typer.Exit(code=1)

    # App name
    if not app_name:
        app_name = typer.prompt(
            "Enter the app name",
            default="app_name",
            prompt_suffix=" (e.g., reddit, youtube): ",
        ).strip()
    validate_pattern(app_name, "app name")
    app_name = app_name.lower()
    if not output_dir:
        path_str = typer.prompt(
            "Enter the output directory for the project",
            default=str(Path.cwd()),
            prompt_suffix=": ",
        ).strip()
        output_dir = Path(path_str)

    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Created output directory at '{output_dir}'[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to create output directory '{output_dir}': {e}[/red]")
            raise typer.Exit(code=1) from e
    elif not output_dir.is_dir():
        console.print(f"[red]❌ Output path '{output_dir}' exists but is not a directory.[/red]")
        raise typer.Exit(code=1)

    # Integration type
    if not integration_type:
        integration_type = typer.prompt(
            "Choose the integration type",
            default="agentr",
            prompt_suffix=" (api_key, oauth, agentr, none): ",
        ).lower()
    if integration_type not in ("api_key", "oauth", "agentr", "none"):
        console.print("[red]❌ Integration type must be one of: api_key, oauth, agentr, none[/red]")
        raise typer.Exit(code=1)

    console.print("[blue]🚀 Generating project using cookiecutter...[/blue]")
    try:
        cookiecutter(
            "https://github.com/AgentrDev/universal-mcp-app-template.git",
            output_dir=str(output_dir),
            no_input=True,
            extra_context={
                "app_name": app_name,
                "integration_type": integration_type,
            },
        )
    except Exception as exc:
        console.print(f"❌ Project generation failed: {exc}")
        raise typer.Exit(code=1) from exc

    project_dir = output_dir / f"{app_name}"
    console.print(f"✅ Project created at {project_dir}")


@app.command()
def preprocess(
    schema_path: Path = typer.Option(None, "--schema", "-s", help="Path to the OpenAPI schema file."),
    output_path: Path = typer.Option(None, "--output", "-o", help="Path to save the processed schema."),
):
    from universal_mcp.utils.openapi.preprocessor import run_preprocessing

    """Preprocess an OpenAPI schema using LLM to fill or enhance descriptions."""
    run_preprocessing(schema_path, output_path)


@app.command()
def split_api(
    input_app_file: Path = typer.Argument(..., help="Path to the generated app.py file to split"),
    output_dir: Path = typer.Option(..., "--output-dir", "-o", help="Directory to save the split files"),
    package_name: str = typer.Option(
        None, "--package-name", "-p", help="Package name for absolute imports (e.g., 'hubspot')"
    ),
):
    """Splits a single generated API client file into multiple files based on path groups."""
    from universal_mcp.utils.openapi.api_splitter import split_generated_app_file

    if not input_app_file.exists() or not input_app_file.is_file():
        console.print(f"[red]Error: Input file {input_app_file} does not exist or is not a file.[/red]")
        raise typer.Exit(1)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created output directory: {output_dir}[/green]")
    elif not output_dir.is_dir():
        console.print(f"[red]Error: Output path {output_dir} is not a directory.[/red]")
        raise typer.Exit(1)

    try:
        split_generated_app_file(input_app_file, output_dir, package_name)
        console.print(f"[green]Successfully split {input_app_file} into {output_dir}[/green]")
    except Exception as e:
        console.print(f"[red]Error splitting API client: {e}[/red]")

        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
