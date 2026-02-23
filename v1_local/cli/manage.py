import sys
import os
import typer

# Add the project root to the python path so we can import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.auth import issue_key
from shared.database import init_db, get_connection, delete_expired_keys

app = typer.Typer(help="Krypton Admin CLI")

@app.command()
def add_friend(name: str, ttl_hours: int = typer.Option(3, help="Time to live in hours")):
    """
    Issue a new API key for a friend directly (Admin only).
    """
    try:
        key = issue_key(name, ttl_hours)
        typer.secho(f"\nSuccess! API Key created for '{name}'.", fg=typer.colors.GREEN)
        typer.secho(f"Key: {key}", fg=typer.colors.CYAN, bold=True)
        typer.secho(f"This key will expire in {ttl_hours} hours.\n", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"Error creating key: {e}", fg=typer.colors.RED)

@app.command()
def request_key(name: str, server_url: str = typer.Option("http://127.0.0.1:8000", help="URL of the Krypton gateway")):
    import httpx
    typer.echo(f"Requesting key from {server_url} for '{name}'...")
    try:
        response = httpx.post(
            f"{server_url}/request-key",
            json={"name": name},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            typer.secho(f"\nSuccess! Server generated a key for '{name}'.", fg=typer.colors.GREEN)
            typer.secho(f"Key: {data['key']}", fg=typer.colors.CYAN, bold=True)
            typer.secho(f"This key will expire in {data['expires_in_hours']} hours.\n", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Failed to request key: HTTP {response.status_code}\nDetails: {response.text}", fg=typer.colors.RED)
    except httpx.RequestError as e:
        typer.secho(f"Could not connect to server at {server_url}: {e}", fg=typer.colors.RED)

@app.command()
def list_friends():
    delete_expired_keys()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key_string, owner_name, expires_at, is_active FROM api_keys")
        rows = cursor.fetchall()
        
        if not rows:
            typer.echo("No keys found in the database. Add a friend first!")
            return

        typer.secho(f"\n--- Active Krypton Friends ---", bold=True)
        for row in rows:
            key_str, owner, expires, active = row
            status = typer.style("Active", fg=typer.colors.GREEN) if active else typer.style("Inactive", fg=typer.colors.RED)
            masked_key = f"{key_str[:6]}...{key_str[-4:]}"
            typer.echo(f"User: {owner}  |  Key: {masked_key}  |  Expires: {expires}  |  Status: {status}")
        typer.echo("\n")

@app.command()
def init():
    confirm = typer.confirm("This will drop any existing api_keys table. Are you sure?")
    if confirm:
        init_db()
        typer.secho("Database initialized.", fg=typer.colors.GREEN)
    else:
        typer.echo("Aborted.")

if __name__ == "__main__":
    app()
