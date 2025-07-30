from datetime import datetime
import webbrowser
import typer
from rich import print, box
from rich.table import Table
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
import httpx
from . import utils
from .utils import AuthError
# from .cliconfig import settings
from dotenv import load_dotenv
import os

app = typer.Typer()
console = Console()

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

# API_BASE_URL = f"{settings.api_base_url}"

@app.command(help="Shorten Url")
def shorten(url = typer.Option(..., prompt=True, help="The URL that needs to be shortened")):
    try:
        r = utils.make_authenticated_request(
            url= f"{API_BASE_URL}/shorten",
            method="POST",
            data= {"original": url},
            status_message="[green]Generating Short Url...[/green]")
        
        res = r.json()
        
        content = f"""
        [cyan]Original:[/cyan] {url}
        ID: {res.get('id')}
        [magenta]Short URL:[/magenta] {res.get('short_url')}
        [yellow]Short Code:[/yellow] {res.get('short_code')} """

        panel = Panel(content, 
                      title="URL Shortened Successfully !",
                      title_align='center',
                      padding=(1,2),
                      border_style='green')
        
        print(panel)
        
    except AuthError as e:
        print(e)
        raise typer.Exit(1)
    
@app.command(help="Get Url by ID")
def get_by_id(id = typer.Option(..., prompt=True, help="ID of the URL to search")):
    try:
        r = utils.make_authenticated_request(
            url=f"{API_BASE_URL}/by-id/{id}",
            status_message = f"[green]Fetching Url with ID {id}[/green]"
        )

        url_data = r.json()

        created_date = datetime.fromisoformat(url_data['created_at'].replace('Z', '+00:00'))
        formatted_date = created_date.strftime("%d-%m-%Y at %H:%M")
        
        # Create the content
        content = f"""[cyan]Original URL:[/cyan] {url_data.get('original')}
[magenta]Short URL:[/magenta] {url_data.get('short_url')}
[yellow]Short Code:[/yellow] {url_data.get('short_code')}
[green]Clicks:[/green] {url_data.get('clicks')}
[blue]Created At:[/blue] {formatted_date}"""
        
        # Create and display the panel
        panel = Panel(
            content,
            title="URL",
            title_align="center",
            border_style="blue",
            padding=(1, 2)
        )
        
        print(panel)

    except AuthError as e:
        print(e)
        raise typer.Exit(1)
    

@app.command(help="Redirect to original URL")
def redirect(short_code = typer.Option(..., prompt=True, help="Short Code of the URL")):
    try:
        r = utils.make_authenticated_request(
            url = f"{API_BASE_URL}/{short_code}",
            method="GET",
            status_message="[green]Fetching Url...[/green]"
        )
        
        if r.status_code in [301, 302, 307, 308]:  # Redirect status codes
            original_url = r.headers.get('location', 'URL not found')
            
            content = f"""[cyan]Short Code:[/cyan] {short_code}
[magenta]Original URL:[/magenta] {original_url}
[green]Status:[/green] Redirecting..."""
            
            panel = Panel(
                content,
                title="URL Found!",
                title_align="center",
                border_style="blue",
                padding=(1, 2)
            )
            
            print(panel)

            open_browser = typer.confirm("Open this URL in your browser?", default=True)
            if open_browser:
                try:
                    webbrowser.open(original_url)
                    print("[green]Yayy, URL opened in your original browser![/green]")
                except Exception as e:
                    print("[red]Uh oh, Failed to open URL in browser[/red]")
                    print(f"[yellow]You can manually visit: {original_url}[/yellow]")
            else:
                print(f"[yellow]You can manually visit: {original_url}[/yellow]")

        else:
            print(f"[red]Unexpected Error: {r.status_code}[/red]")
    except AuthError as e:
        print(e)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print(f"[red]Network Error: {e}[red]")
        typer.Exit(1)


@app.command(help="Custom Short Code")
def customize(url_id = typer.Option(..., prompt=True, help="ID of the URL"),
              new_short_code = typer.Option(..., prompt=True, help="Cutom Short Code of URL")):
    try:
        r = utils.make_authenticated_request(
            url= f"{API_BASE_URL}/{url_id}",
            method="PUT",
            data={'short_code': new_short_code},
            status_message="[green]Customising your URL...[/green]"
        )

        url_data = r.json()

        created_date = datetime.fromisoformat(url_data['created_at'].replace('Z', '+00:00'))
        formatted_date = created_date.strftime("%d-%m-%Y at %H:%M")
        
        # Create the content
        content = f"""ID: {url_data.get('id')}
[cyan]Original URL:[/cyan] {url_data.get('original')}
[magenta]Short URL:[/magenta] {url_data.get('short_url')}
[yellow]Short Code:[/yellow] {url_data.get('short_code')}
[green]Clicks:[/green] {url_data.get('clicks')}
[blue]Created At:[/blue] {formatted_date}"""
        
        # Create and display the panel
        panel = Panel(
            content,
            title="URL Shortened Successfully!",
            title_align="center",
            border_style="green",
            padding=(1, 2)
        )
        
        print(panel)

    except AuthError as e:
        print(e)
        raise typer.Exit(1)
    
@app.command(help="Delete URL")
def delete(id = typer.Option(..., prompt=True, help="ID of URL to be deleted")):
    confirm = typer.confirm("Are you sure you want to delete this URL?")
    if not confirm:
        print("[yellow]URL deletion cancelled[/yellow]")
        raise typer.Exit()
    try:
        r = utils.make_authenticated_request(
            url=f"{API_BASE_URL}/{id}",
            method="DELETE",
        )

        print("[green]URL deleted successfully![/green]")

    except AuthError as e:
        print(e)
        raise typer.Exit(1)
    
@app.command(help="Get Analytics of a URL")
def analytics(id = typer.Option(..., prompt=True, help="ID of URL")):
    try:
        r = utils.make_authenticated_request(
            url=f"{API_BASE_URL}/analytics/{id}",
            method="GET",
            status_message="[green]Fetching Analytics...[green]"
        )

        data= r.json()
        
        table = Table(show_header=True, box=box.ROUNDED, padding=(0, 1), header_style='bold cyan')

        table.add_column("IP Address", style="bright_blue", max_width=30)
        table.add_column("Timestamp", style="bright_magenta", justify='center' ,min_width=15)

        for click in data['click_details']:
            time_stamp = datetime.fromisoformat(click['timestamp'].replace('Z', '+00:00'))
            formatted_ts = time_stamp.strftime("%d-%m-%Y at %H:%M")

            table.add_row(
                f"[bold]{click['ip_address']}[/bold]",
                formatted_ts
            )

        content = Text.from_markup(f"""
        [cyan]ID[/cyan]: {data.get("url_id")}
        [magenta]Original[/magenta]: {data.get('original')}
        [yellow]Short Url[/yellow]: {data.get('short_url')}
        [green]Total Clicks[/green]: {data.get('total_clicks')}""")

        separator = Text("\n" + "─" * 50, style="dim")
        table_title = Text("Click Details:", style="bold yellow")
    
    # Group all content together
        panel_content = Group(
            content,
            Text(""),
            Align.center(separator),
            Align.center(table_title),
            Text(""),  # Empty line for spacing
            Align.center(table)
        )
    
        # Create the panel with all content
        panel = Panel(
            panel_content, 
            title="Analytics", 
            title_align='center', 
            border_style='green', 
            padding=(1, 2)
        )

        print(panel)
        
    except AuthError as e:
        print(e)
        raise typer.Exit(1)