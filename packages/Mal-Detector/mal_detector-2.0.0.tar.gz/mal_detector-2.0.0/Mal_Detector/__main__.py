from .banner import show_banner
from .cli import ask_user_option
from .vt_api import scan_url, scan_file, save_result_as_html
from rich.console import Console
import os

def main():
    console = Console()
    show_banner()
    choice = ask_user_option()

    if choice == "1":
        url = console.input("[bold green]Enter the URL: [/bold green]")
        result = scan_url(url)
        saved_path = save_result_as_html(result, url)
    else:
        file_path = console.input("[bold green]Enter file path: [/bold green]")
        result = scan_file(file_path)
        saved_path = save_result_as_html(result, os.path.basename(file_path))

    console.rule("[bold blue]Scan Result")
    console.print(result, highlight=True)
    console.print(f"\n[bold green]\u2713 Result saved to:[/bold green] [yellow]{saved_path}[/yellow]")

if __name__ == "__main__":
    main()
