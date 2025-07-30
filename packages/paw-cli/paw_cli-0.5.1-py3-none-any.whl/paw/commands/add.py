import typer
import re
import shutil
from pathlib import Path
from rich.console import Console
from .. import utils

app = typer.Typer(
    name="add",
    help="向当前项目中添加新内容, 如章节、图片、参考文献等。",
    no_args_is_help=True
)
console = Console()

def slugify(text: str) -> str:
    """将文本转换为适合做文件名的 slug 格式"""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text

def _add_chapter_logic(title: str):
    project_paths = utils.get_project_paths()
    manuscript_dir = project_paths["manuscript"]
    
    max_num = 0
    for f in manuscript_dir.glob("*.md"):
        match = re.match(r'(\d+)-', f.name)
        if match:
            max_num = max(max_num, int(match.group(1)))
    
    new_num = max_num + 1
    slug_title = slugify(title)
    new_filename = f"{new_num:02d}-{slug_title}.md"
    new_filepath = manuscript_dir / new_filename

    try:
        with open(new_filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
        console.print(f"[green]✓ Created new chapter:[/green] {new_filepath}")
    except Exception as e:
        console.print(f"[bold red]Error creating chapter file: {e}[/bold red]")
        raise typer.Exit(1)

@app.command("chapter", help="添加一个新章节。 Aliases: 'chap', 'zhang'.")
def add_chapter(title: str = typer.Argument(..., help="新章节的标题。")):
    _add_chapter_logic(title)

@app.command("chap", hidden=True)
def add_chapter_alias_chap(title: str = typer.Argument(..., help="新章节的标题。")):
    _add_chapter_logic(title)

@app.command("zhang", hidden=True)
def add_chapter_alias_zhang(title: str = typer.Argument(..., help="新章节的标题。")):
    _add_chapter_logic(title)


def _add_figure_logic(source_path: Path, caption: str | None):
    project_paths = utils.get_project_paths()
    figures_dir = project_paths["figures"]

    dest_path = figures_dir / source_path.name
    if dest_path.exists():
        if not typer.confirm(f"'{dest_path.name}' already exists. Overwrite?"):
            console.print("Aborted.")
            raise typer.Exit()
            
    try:
        shutil.copy(source_path, dest_path)
        console.print(f"[green]✓ Copied image to:[/green] {dest_path}")
    except Exception as e:
        console.print(f"[bold red]Error copying figure: {e}[/bold red]")
        raise typer.Exit(1)

    caption_text = caption if caption else "Your caption here."
    figure_slug = slugify(dest_path.stem)
    md_code = f"![{caption_text}](./figures/{dest_path.name}){{{{#fig:{figure_slug}}}}}"

    console.print("\n[bold]Markdown code to insert:[/bold]")
    console.print(md_code, style="cyan")

@app.command("figure", help="添加一张图片。 Aliases: 'fig', 'tupian'.")
def add_figure(
    source_path: Path = typer.Argument(..., help="源图片文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True),
    caption: str = typer.Option(None, "--caption", "-c", help="图片的标题。"),
):
    _add_figure_logic(source_path, caption)

@app.command("fig", hidden=True)
def add_figure_alias_fig(source_path: Path = typer.Argument(..., help="源图片文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True), caption: str = typer.Option(None, "--caption", "-c", help="图片的标题。")):
    _add_figure_logic(source_path, caption)

@app.command("tupian", hidden=True)
def add_figure_alias_tupian(source_path: Path = typer.Argument(..., help="源图片文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True), caption: str = typer.Option(None, "--caption", "-c", help="图片的标题。")):
    _add_figure_logic(source_path, caption)


def _add_bib_logic(source_path: Path):
    if source_path.suffix != ".bib":
        console.print(f"[bold red]Error:[/bold] File must be a '.bib' file.")
        raise typer.Exit(1)

    project_paths = utils.get_project_paths()
    resources_dir = project_paths["resources"]
    
    dest_path = resources_dir / source_path.name
    if dest_path.exists():
        if not typer.confirm(f"'{dest_path.name}' already exists. Overwrite?"):
            console.print("Aborted.")
            raise typer.Exit()

    try:
        shutil.copy(source_path, dest_path)
        console.print(f"[green]✓ Copied bibliography to:[/green] {dest_path}")
    except Exception as e:
        console.print(f"[bold red]Error copying .bib file: {e}[/bold red]")
        raise typer.Exit(1)

    relative_path = f"resources/{dest_path.name}"
    utils.update_yaml_list(project_paths["frontmatter"], "bibliography", relative_path)

@app.command("bib", help="添加一个 .bib 参考文献文件。 Alias: 'wenxian'.")
def add_bib(source_path: Path = typer.Argument(..., help="源 .bib 文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True)):
    _add_bib_logic(source_path)

@app.command("wenxian", hidden=True)
def add_bib_alias_wenxian(source_path: Path = typer.Argument(..., help="源 .bib 文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True)):
    _add_bib_logic(source_path)
