import typer

from .core import login, logout, status, verify

app = typer.Typer(
    add_completion=False,
    help="🔑 Keyed Login — manage access to the keyed-extras sponsorware private package index via GitHub OAuth.",
)


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        ctx.invoke(login)
        ctx.exit()

app.command()(login)
app.command()(status)
app.command()(verify)
app.command()(logout)


def main():
    """Entry point for the CLI application."""
    app()
