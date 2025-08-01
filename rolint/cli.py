import typer
from pathlib import Path

from rolint.main import run_linter

##Main entry point for command line with rolint
app = typer.Typer(help="Rolint - Linter for robotics code (C, C++, Python)")

@app.command()
def check(
    path: Path = typer.Argument(..., help="Path to folder or file to lint"),
    lang: str = typer.Option(None, "--lang", "-l", help="Optional: Force language (c | cpp | python)"),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text | json")
):
    """
    Run safety checks on code.

    Examples: \n
      For checking with specific options: rolint check --lang c examples/file.c \n
      For default linting: rolint examples/              \n
    """
    run_linter(path, lang=lang, output_format=output)


