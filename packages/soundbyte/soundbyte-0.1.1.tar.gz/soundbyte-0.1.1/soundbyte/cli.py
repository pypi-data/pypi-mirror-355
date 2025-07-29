import typer
from typing import Optional
from soundbyte.commands import supervised_classification


app = typer.Typer(
    name="soundbyte",
    help="A simple toolkit for JSON data handling and visualization",
    add_completion=False,
)

# Add subcommands
app.add_typer(supervised_classification.app, name="supervised_classification")

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", help="Show the application version and exit."
    )
):
    """SoundByte - A simple toolkit for JSON data handling and visualization."""
    if version:
        typer.echo(f"SoundByte version: Update in Progress")
        raise typer.Exit()

if __name__ == "__main__":
    app()
