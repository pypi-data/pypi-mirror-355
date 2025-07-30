import typer
import shutil
from rich.console import Console
from .. import utils

console = Console()

def shake():
    """
    清理项目输出目录 (`output/`)。
    """
    project_paths = utils.get_project_paths()
    output_dir = project_paths.get("output")

    if not output_dir or not output_dir.is_dir():
        console.print("[bold red]Error:[/bold red] 'output' directory not found in this project.")
        raise typer.Exit(1)

    console.print("🐾 [italic]shake shake...[/italic] Cleaning up those pesky temporary files...")
    
    try:
        # 删除目录下的所有内容，但不删除目录本身
        for item in output_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        console.print("✨ All clean! Ready for the next writing session.")
    except Exception as e:
        console.print(f"[bold red]Error during cleanup: {e}[/bold red]")
        raise typer.Exit(1)
