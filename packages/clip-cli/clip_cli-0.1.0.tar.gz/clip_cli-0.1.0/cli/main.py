import typer
from rich import print
from . import user, auth, url

app = typer.Typer()

app.add_typer(auth.app)
app.add_typer(user.app, name="user", help="User-specific commands")
app.add_typer(url.app, name="url", help="Url-specific commands")

@app.command(help="Welcome greeting")
def hi(name: str = typer.Option(..., prompt = True, help="Name of the user")):
    print(f"Hi {name}, welcome to clip. your very own url shortner!")

if __name__ == '__main__':
    app()