import shutil
import typer
from rich.console import Console
from rich.table import Table

console = Console()

def _check_logic():
    """检查依赖的核心逻辑,返回是否全部找到"""
    table = Table(title="PAW Dependency Status")
    table.add_column("Dependency", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Path / Info", justify="left", style="green")

    dependencies = {
        "Pandoc": "pandoc",
        "LaTeX (pdflatex)": "pdflatex",
        "LaTeX (xelatex)": "xelatex",
    }

    all_found = True
    for name, cmd in dependencies.items():
        path = shutil.which(cmd)
        if path:
            table.add_row(name, "[bold green]✓ Found[/bold green]", path)
        else:
            all_found = False
            info_text = f"'{cmd}' not found. Please install it."
            if "latex" in name.lower():
                info_text += " We recommend installing a full LaTeX distribution like TeX Live, MacTeX, or MiKTeX."
            table.add_row(name, "[bold red]✗ Missing[/bold red]", info_text)

    console.print(table)
    return all_found

def check():
    """
    检查 PAW 所需的核心依赖 (Pandoc, LaTeX) 是否已安装。
    """
    console.print("[bold] Checking for required dependencies...[/bold]")
    all_found = _check_logic()
    if not all_found:
        console.print("\n[yellow]Some dependencies are missing. Please install them to ensure all features work correctly.[/yellow]")
        raise typer.Exit(code=1)
    else:
        console.print("\n[bold green]✓ All core dependencies are installed. PAW is ready to pounce! 🐾[/bold green]")

def check_purr():
    """
    检查依赖的 'purr' 版本。
    """
    console.print(" Purring... checking system health...")
    all_found = _check_logic()
    if not all_found:
        console.print("\n[yellow]Hiss... Some dependencies are missing.[/yellow]")
        raise typer.Exit(code=1)
    else:
        console.print("\n[bold magenta]Purrrrrr... Everything is purrfect! 🐾[/bold magenta]")

