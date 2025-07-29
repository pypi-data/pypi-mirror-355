from rich.console import Console

def ask_user_option():
    console = Console()
    console.print("\n[cyan]What do you want to scan?[/cyan]")
    console.print("[bold yellow]1.[/bold yellow] URL")
    console.print("[bold yellow]2.[/bold yellow] File")
    while True:
        choice = console.input("\n[bold blue]Enter your choice (1/2): [/bold blue]")
        if choice in ["1", "2"]:
            return choice
        console.print("[red]Invalid choice. Try again.[/red]")
