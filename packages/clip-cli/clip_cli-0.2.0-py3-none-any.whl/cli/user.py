from datetime import datetime
import typer
from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import httpx
from . import utils
from .utils import AuthError
# from .cliconfig import settings
from dotenv import load_dotenv
import os

app = typer.Typer()
console = Console()

load_dotenv()

API_BASE_USER = os.getenv("API_BASE_USER")


@app.command(help="Register user")
def register(full_name: str = typer.Option(..., prompt=True, help="The name of the user"),
             email: str = typer.Option(..., prompt=True, help="The email of the user"),
             password: str = typer.Option(..., prompt=True, help="The password of the user")):
    
    try:
        with console.status("[bold green]Creating User...[/bold green]") as status:
            r = httpx.post(f"{API_BASE_USER}/register",
                            json={"full_name": full_name, "email": email, "password": password})
        
        if r.status_code == 409:
            print("[red]User already exists[/red]")
            raise typer.Exit(1)

        r.raise_for_status()
        res = r.json()

        created_date = datetime.fromisoformat(res['created_at'].replace('Z', '+00:00'))
        formatted_date = created_date.strftime("%d-%m-%Y at %H:%M")

        content = f"""ID: {res.get('id')}
[cyan]Full Name: [/cyan] {res.get('full_name')}
[magenta]Email: [/magenta]{res.get('email')}
[yellow]URLs Created: [/yellow] {res.get('urls_created')}
[green]User Created At: [/green] {formatted_date}"""
        
        panel = Panel(content,
                      title="User Created Successfully!",
                      title_align='center',
                      border_style='green',
                      padding=(1,2))
        
        print(panel)

    except httpx.HTTPStatusError as e:
        print(f"[red]Oops! HTTP error: {e}[/red]")
        raise typer.Exit(code=1)
    
    except httpx.RequestError as e:
        print(f"[red]Oops! Network error: {e}[/red]")
        raise typer.Exit(code=1)
    

@app.command(help="Show user profile")
def show_me():
    try:
        r = utils.make_authenticated_request(url = f"{API_BASE_USER}/profile", status_message="[green]Fetching Profile...")

        user = r.json()
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))

        table.add_column("Full Name", style="bright_blue", min_width=15)
        table.add_column("Email", style="bright_magenta", justify="center", min_width=20)
        table.add_column("URLs Created", style="bright_green", justify="center", min_width=10)
        table.add_column("Profile Created At", style="bright_yellow",justify="center", min_width=12)

        created_date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        formatted_date = created_date.strftime("%d/%m %H:%M")

        table.add_row(
            user['full_name'],
            user['email'],
            str(user['urls_created']),
            formatted_date
        )

        dashboard_panel = Panel(
            table,
            title=f"Profile",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        console.print(dashboard_panel)

    except AuthError as e:
        print(e)
        raise typer.Exit(1)

@app.command(help="Update Profile")
def update_profile():

    print("Update your profile (press Enter to skip any field):")
    
    full_name = Prompt.ask("Full Name", default="")
    email = Prompt.ask("Email", default="")
    
    data = {}
    if full_name.strip():
        data["full_name"] = full_name.strip()
    if email.strip():
        data["email"] = email.strip()
    
    if not data:
        print("[yellow]No changes provided. Profile not updated.[/yellow]")
        return

    try:
        r = utils.make_authenticated_request(
        url=f"{API_BASE_USER}/update", 
        method="PATCH",
        data=data,
        status_message="[green]Updating your profile..."
        )

        print("[green]Yayy, Profile updated successfully![/green]")
        
        updated_user = r.json()

        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))

        table.add_column("Full Name", style="bright_blue", min_width=15)
        table.add_column("Email", style="bright_magenta", justify="center", min_width=20)

        table.add_row(
            updated_user['full_name'],
            updated_user['email'],
        )

        dashboard_panel = Panel(
            table,
            title=f"Updated Profile",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        console.print(dashboard_panel)

    except AuthError as e:
        print(e)
        raise typer.Exit(1)

@app.command(help="Update Password")
def update_password(old_password: str = typer.Option(..., prompt=True, help="Old password of User"),
                    new_password: str = typer.Option(..., prompt=True, help="New Password of User")):
    
    data = {
        "old_password": old_password,
        "new_password": new_password
    }

    try :
        r = utils.make_authenticated_request(
            url=f"{API_BASE_USER}/password", 
            method="PUT", 
            data=data, 
            status_message="[green]Updating your precious password...")
        
        print("[green]Yayy, Password updated successfully!")

    except AuthError as e:
        print(e)
        raise typer.Exit(1)

@app.command(help="Delete user")
def delete_profile():
    confirm = typer.confirm("Are you sure you want to delete your account and ALL associated data?")
    if not confirm:
        print("[yellow]Account deletion cancelled.[/yellow]")
        raise typer.Exit()
    
    try:
        r = utils.make_authenticated_request(
            url=f"{API_BASE_USER}/delete",
            method="DELETE",
            status_message="[green]Deleting your profile..."
        )

        print("[bold green]Profile deleted successfully[/bold green]")
        print("[blue]Goodbye stranger :([/blue]")

    except AuthError as e:
        print(e)
        raise typer.Exit(1)

@app.command(help="Get Dashboard")
def dashboard():
    try:
        r = utils.make_authenticated_request(
            url=f"{API_BASE_USER}/dashboard",
            method="GET",
            status_message="[green]Fetching Dashboard...[/green]"
        )

        data = r.json()
        if not data:
            print(Panel("[yellow]Uh oh, No URLs found in your dashboard.[/yellow]",
                        title="Dashboard", border_style='yellow'))
            return
       
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        
        table.add_column("URL", style="bright_blue", max_width=100)
        table.add_column("Code", style="bright_magenta", justify="center", min_width=8)
        table.add_column("Clicks", style="bright_green", justify="center", min_width=4)
        table.add_column("Created At", style="bright_yellow", justify="center", min_width=12)
        
        for item in data:
            # Format date more compactly
            created_date = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            formatted_date = created_date.strftime("%d/%m %H:%M")
            
            # Clean URL display
            url = item['original'].replace('https://', '').replace('http://', '')
            
            table.add_row(
                url,
                f"[bold]{item['short_code']}[/bold]",
                str(item['clicks']),
                formatted_date
            )


        dashboard_panel = Panel(
            table,
            title=f"Dashboard ({len(data)} URLs)",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        console.print(dashboard_panel)

    except AuthError as e:
        print(e)
        raise typer.Exit(1)