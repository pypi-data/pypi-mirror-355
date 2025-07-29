import os
from rich.console import Console

CONFIG_FILE = os.path.expanduser("~/.vt_scan_config")

def get_api_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    else:
        return ask_and_save_api_key()

def ask_and_save_api_key():
    console = Console()
    api_key = console.input("[bold cyan]Enter your VirusTotal API key:[/bold cyan] ")
    with open(CONFIG_FILE, "w") as f:
        f.write(api_key.strip())
    console.print("[green]API key saved in ~/.vt_scan_config[/green]")
    return api_key
