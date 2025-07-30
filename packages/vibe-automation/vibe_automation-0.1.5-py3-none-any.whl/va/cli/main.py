import typer
from .command import login

app = typer.Typer(help="Orby CLI for automating workflows")

# Add 'auth' group
app.add_typer(login.app, name="auth", help="Authentication commands")

if __name__ == "__main__":
    app()
