import typer

from .core import login, logout, status, verify

app = typer.Typer(
    add_completion=False,
    help="🔑 Keyed Login - access your sponsorware",
    no_args_is_help=True,
)

app.command()(login)
app.command()(status)
app.command()(verify)
app.command()(logout)


def main():
    """Entry point for the CLI application."""
    app()
