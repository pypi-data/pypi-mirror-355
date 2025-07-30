import shutil
import typer
import subprocess
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .. import utils

console = Console()

def find_executable(name: str) -> str | None:
    """
    一个更健壮的、用于查找可执行文件的函数，特别为 macOS 优化。
    """
    path = shutil.which(name)
    if path:
        return path
    
    if sys.platform == "darwin":
        mactex_path = Path("/Library/TeX/texbin") / name
        if mactex_path.exists() and os.access(mactex_path, os.X_OK):
            return str(mactex_path)
            
    return None

def _check_logic():
    """检查依赖的核心逻辑,返回是否全部找到"""
    table = Table(title="PAW Dependency Status")
    table.add_column("Dependency", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Path / Info", justify="left", style="green")

    all_found = True

    # --- 检查 Pandoc ---
    pandoc_path = utils.get_pandoc_path()
    if Path(pandoc_path).is_file():
        try:
            result = subprocess.run([pandoc_path, "--version"], capture_output=True, text=True, check=True, encoding='utf-8')
            version = result.stdout.splitlines()[0]
            table.add_row("Pandoc", "[bold green]✓ Found[/bold green]", f"{version}\n@ {pandoc_path}")
        except Exception:
            table.add_row("Pandoc", "[bold green]✓ Found[/bold green]", f"Found at {pandoc_path}, but couldn't get version.")
    else:
        all_found = False
        table.add_row("Pandoc", "[bold red]✗ Missing[/bold red]", "Please install Pandoc or bundle it with PAW.")

    # --- 检查 LaTeX ---
    for latex_cmd in ["pdflatex", "xelatex"]:
        path = find_executable(latex_cmd)
        if path:
            table.add_row(f"LaTeX ({latex_cmd})", "[bold green]✓ Found[/bold green]", path)
        else:
            table.add_row(f"LaTeX ({latex_cmd})", "[yellow]! Optional[/yellow]", f"'{latex_cmd}' not found. Needed for PDF output.")

    console.print(table)
    return all_found

def check():
    """检查 PAW 所需的核心依赖 (Pandoc, LaTeX) 是否已安装。"""
    console.print("[bold] Checking for required dependencies...[/bold]")
    _check_logic()
    
def check_purr():
    """检查依赖的 'purr' 版本。"""
    console.print(" Purring... checking system health...")
    all_found = _check_logic()
    if not all_found and not Path(utils.get_pandoc_path()).is_file():
         console.print("\n[yellow]Hiss... Pandoc is missing.[/yellow]")
    else:
        console.print("\n[bold magenta]Purrrrrr... Everything is purrfect! 🐾[/bold magenta]")
