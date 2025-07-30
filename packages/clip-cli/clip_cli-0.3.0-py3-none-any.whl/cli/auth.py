import typer
from rich import print
from rich.console import Console
import httpx
from . import utils
# from .cliconfig import settings
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE = os.getenv("API_BASE")

app = typer.Typer()
console = Console()

@app.command(help="Login")
def login(email: str = typer.Option(..., prompt=True, help="Email of the user"),
          password: str = typer.Option(..., prompt=True, help="Password of the user")):
    
    data = {
        "username": email,
        "password": password
    }

    try:
        with console.status("[bold green]Logging in...", spinner="dots") as status:
            r = httpx.post(f"{API_BASE}/login", data=data, timeout=10)

        if r.status_code == 200:
            token = r.json()["access_token"]
            token_path = utils.get_token_path()
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(token)
            print("[green]Yayy Login Successfull![/green]")
        else:
            print(f"[red]Uh oh! Login failed: {r.json()['detail']}[/red]")

    except httpx.RequestError as e:
        print(f"[red]No way! Request error {e}[/red]")

@app.command(help="Logout")
def logout():
    token = utils.get_saved_token()

    if not token:
        print("[yellow]Smarty Pants, You are not logged in[/yellow]")
        raise typer.Exit()
    
    # headers = {"Authorization": f"Bearer {token}"}
    # try:
    #     with console.status("[green]Logging you out..[/green]") as status:
    #         r = httpx.post(f"{API_BASE}/logout", headers=headers)
    # except httpx.ConnectError as e:
    #     print("[red]Server unreachable. You are stuck with us :( [/red]")
    #     raise typer.Exit()

    # if r.status_code == 200:
    utils.delete_token()
    print("[bold green]Logged Out Successfully![/bold green]")
    print("[blue]You left without a goodbye tho :([/blue]")
    # else:
    #     print("[red]Failed to log out[/red]")
    #     print("[yellow]Haha, Sorry not sorry[/yellow]")
