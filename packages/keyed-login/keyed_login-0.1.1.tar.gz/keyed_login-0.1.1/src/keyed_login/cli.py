import typer

from .core import login, logout, status, verify

app = typer.Typer(
    add_completion=False,
    help="🔑 Keyed Login - access the keyed-extras sponsorware",
)

app.callback(invoke_without_command=True)(login)
app.command()(status)
app.command()(verify)
app.command()(logout)


def main():
    """Entry point for the CLI application."""
    app()
