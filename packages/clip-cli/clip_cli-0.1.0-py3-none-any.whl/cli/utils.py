from pathlib import Path
import httpx
from rich.console import Console

console = Console()

class AuthError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def get_token_path():
    return Path.home() / ".urlshortener" / "token.txt"

def get_saved_token():
    token_path = get_token_path()
    if token_path.exists():
        return token_path.read_text().strip()
    return None

def delete_token():
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()

def make_authenticated_request(url: str, method: str = "GET", data: dict = None, status_message: str = None):
    token = get_saved_token()
    
    if not token:
        raise AuthError("[red]Uh oh, You are not logged in. Please log in to continue[/red]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not status_message:
        status_message = f"[green]Making {method.upper()} request..."
    
    with console.status(status_message) as status:
        if method.upper() == "GET":
            r = httpx.get(url=url, headers=headers, follow_redirects=False)
        elif method.upper() == "POST":
            r = httpx.post(url=url, headers=headers, json=data)
        elif method.upper() == "PUT":
            r = httpx.put(url=url, headers=headers, json=data)
        elif method.upper() == "PATCH":
            r = httpx.patch(url=url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            r = httpx.delete(url=url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    if r.status_code == 401:
        delete_token()
        raise AuthError('[red]Oops! Session expired or invalid token. Please login again.[/red]')
    
    if r.status_code == 422:
        raise AuthError("[red]Haha, nice one. Please enter a valid url next time.[/red]")
    
    # if r.status_code == 404:
    #     raise AuthError(f"[red]Error: Short code not found.[/red]")
            
    if r.status_code not in [200, 201, 204, 307]:
        raise AuthError(f'[red]Error: {r.status_code} - {r.text}[/red]')
    
    return r


