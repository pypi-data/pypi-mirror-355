from rich.console import Console
from rich.panel import Panel

def show_banner():
    banner_text = """

  __  __       _        _____       _            _             
 |  \/  |     | |      |  __ \     | |          | |            
 | \  / | __ _| |______| |  | | ___| |_ ___  ___| |_ ___  _ __ 
 | |\/| |/ _` | |______| |  | |/ _ \ __/ _ \/ __| __/ _ \| '__|
 | |  | | (_| | |      | |__| |  __/ ||  __/ (__| || (_) | |   
 |_|  |_|\__,_|_|      |_____/ \___|\__\___|\___|\__\___/|_|   
                                                               
                                                               
 
"""
    console = Console()
    console.print(Panel(banner_text, title="[bold red]Mal-Detector[/bold red]", subtitle="[bold blue]By Bismoy Ghosh[/bold blue]"))
