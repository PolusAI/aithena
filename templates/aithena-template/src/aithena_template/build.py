from pathlib import Path
import typer
from aithena_template.build_script import build_common as _build_common

app = typer.Typer()

@app.command()
def build(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Input directory")
    ):
    """Build a Python project using the provided configuration file."""

    if config_file is None:
        typer.echo("No configuration file provided.")
        raise typer.Abort()
    
    print("Building project using configuration file:", config_file.as_posix())
    _build_common(config_file)

if __name__ == "__main__":
    app()