import typer
from pathlib import Path
from rich.console import Console
from ..templates import file_templates
from .. import utils

console = Console()

def create_project(project_path: Path, title: str):
    """业务逻辑: 创建完整的项目结构和文件"""
    utils.ensure_paw_dirs()

    console.print(f"🐾 [italic]scratch scratch...[/italic] creating a new territory for [bold cyan]{project_path.name}[/bold cyan]...")

    dirs = ["manuscript", "resources", "figures", "output"]
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        for d in dirs:
            (project_path / d).mkdir(exist_ok=True)
        console.print(" ✓ Directories created.")
    except Exception as e:
        console.print(f"[bold red]Error creating directories: {e}[/bold red]")
        raise typer.Exit(code=1)

    # 最终的文件结构，使用 metadata.yaml 替代 00-frontmatter.md
    files_to_create = {
        "Makefile": file_templates.get_makefile_template(),
        ".gitignore": file_templates.get_gitignore_template() or "...", # 如果模板为空，提供默认值
        "README.md": file_templates.get_readme_template(project_path.name) or "...", # 同上
        "manuscript/metadata.yaml": file_templates.get_metadata_template(title),
        "manuscript/01-introduction.md": file_templates.get_introduction_template(),
        "resources/bibliography.bib": "# Your references go here",
    }

    try:
        for file_path, content in files_to_create.items():
            if content and content != "...":
                (project_path / file_path).write_text(content, encoding='utf-8')
        console.print(" ✓ Template files created.")
    except Exception as e:
        console.print(f"[bold red]Error creating files: {e}[/bold red]")
        raise typer.Exit(code=1)
        
    console.print(
        f"\n[bold green]Success![/bold green] "
        f"Project '{project_path.name}' is ready!"
    )
    console.print(
        "\n[bold yellow]Important:[/bold yellow] All project settings are now in "
        "[cyan]manuscript/metadata.yaml[/cyan]."
    )
    console.print(f"\n[bold]Next steps:[/bold]\n"
                  f"1. `cd {project_path.name}`\n"
                  f"2. `paw build` to compile your document.\n"
                  )
    console.print(
        "[bold red]Warning:[/bold red] "
        "Please do not use 'sudo' to run 'paw' commands, "
        "as it will cause permission issues."
    )


def new(title: str = typer.Argument(..., help="新论文的项目标题。")):
    """
    创建一个新的 PAW 学术项目。
    """
    project_name_slug = "".join(c for c in title.lower() if c.isalnum() or c in " -").replace(" ", "-")
    project_path = Path.cwd() / project_name_slug

    if project_path.exists():
        console.print(f"[bold red]Error:[/] Directory '[cyan]{project_name_slug}[/]' already exists.")
        overwrite = typer.confirm("Do you want to overwrite it? (This might be risky)")
        if not overwrite:
            console.print("Aborted.")
            raise typer.Exit()

    create_project(project_path, title)
