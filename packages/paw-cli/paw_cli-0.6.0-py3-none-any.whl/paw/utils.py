import shutil
import re
import io
import sys
from pathlib import Path
import typer
from rich.console import Console
from . import config
from ruamel.yaml import YAML
from pybtex.database import parse_file as parse_bib_file

console = Console()
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

def get_pandoc_path() -> str:
    """智能地获取 Pandoc 的路径。"""
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_dir = Path(sys._MEIPASS)
            bundled_pandoc = bundle_dir / 'pandoc'
            if bundled_pandoc.exists():
                return str(bundled_pandoc)
    except Exception:
        pass
    
    system_pandoc = shutil.which("pandoc")
    if system_pandoc:
        return system_pandoc
    return "pandoc"


def read_yaml_file(file_path: Path) -> dict:
    """ (最终稳定版) 读取一个 YAML 文件并返回其内容。 """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
        return data or {}
    except Exception as e:
        console.print(f"[bold red]Error reading YAML file {file_path}: {e}[/bold red]")
        raise typer.Exit(1)


def write_yaml_file(file_path: Path, data: dict):
    """ (最终稳定版) 将数据安全地写回 YAML 文件。 """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
    except Exception as e:
        console.print(f"[bold red]Error writing YAML file {file_path}: {e}[/bold red]")
        raise typer.Exit(1)


def ensure_paw_dirs():
    """确保 PAW 全局资源目录存在"""
    try:
        config.PAW_HOME_DIR.mkdir(exist_ok=True)
        config.CSL_DIR.mkdir(exist_ok=True)
        config.TEMPLATES_DIR.mkdir(exist_ok=True)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold] Could not create PAW home directories in '{config.PAW_HOME_DIR}'.")
        raise typer.Exit(1)


def find_project_root() -> Path | None:
    """通过寻找 Makefile 来确定项目根目录"""
    current_dir = Path.cwd().resolve()
    for _ in range(8):
        if (current_dir / "Makefile").exists() and (current_dir / "manuscript").is_dir():
            return current_dir
        if current_dir.parent == current_dir:
            break
        current_dir = current_dir.parent
    return None


def get_project_paths():
    """获取当前 PAW 项目的关键路径 (最终版)"""
    root = find_project_root()
    if not root:
        console.print("[bold red]Error:[/bold red] Not inside a PAW project. Could not find project root.")
        raise typer.Exit(1)
    
    paths = {
        "root": root,
        "manuscript": root / "manuscript",
        "resources": root / "resources",
        "figures": root / "figures",
        "output": root / "output",
        "metadata": root / "manuscript" / "metadata.yaml"
    }
    if not paths["metadata"].exists():
        console.print(f"[bold red]Error:[/bold red] Metadata file not found at '{paths['metadata']}'")
        raise typer.Exit(1)
    return paths


def update_yaml_key(yaml_path: Path, key: str, value):
    """(最终版) 更新一个纯 YAML 文件中的键值"""
    try:
        data = read_yaml_file(yaml_path)
        
        if key == "bibliography":
            if key not in data or not isinstance(data.get(key), list):
                data[key] = []
            if value not in data[key]:
                data[key].append(value)
        else:
            data[key] = value

        write_yaml_file(yaml_path, data)
        console.print(f"[green]✓ Updated '{key}' in '{yaml_path.name}'.[/green]")

    except Exception as e:
        console.print(f"[bold red]Error updating YAML file: {e}[/bold red]")
        raise typer.Exit(1)


class ResourceHandler:
    """处理 CSL 和 Template 资源的通用逻辑类 (最终版)"""
    def __init__(self, resource_type: str, resource_ext: str, global_dir: Path, yaml_key: str):
        self.resource_type = resource_type
        self.resource_ext = resource_ext
        self.global_dir = global_dir
        self.yaml_key = yaml_key
        ensure_paw_dirs()

    def add(self, source_path: Path):
        if not source_path.exists():
            console.print(f"[bold red]Error:[/bold] File not found at '{source_path}'")
            raise typer.Exit(1)
        if source_path.suffix != self.resource_ext:
            console.print(f"[bold red]Error:[/bold] File must be a '{self.resource_ext}' file.")
            raise typer.Exit(1)
        dest_path = self.global_dir / source_path.name
        try:
            shutil.copy(source_path, dest_path)
            console.print(f"[green]Successfully added '{source_path.name}' to the global {self.resource_type} library.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error adding {self.resource_type}: {e}[/bold red]")
            raise typer.Exit(1)

    def remove(self, name: str):
        if not name.endswith(self.resource_ext):
            name += self.resource_ext
        target_path = self.global_dir / name
        if not target_path.exists():
            console.print(f"[bold red]Error:[/bold] {self.resource_type.capitalize()} '{name}' not found in the global library.")
            raise typer.Exit(1)
        try:
            target_path.unlink()
            console.print(f"[green]Successfully removed '{name}' from the global {self.resource_type} library.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error removing {self.resource_type}: {e}[/bold red]")
            raise typer.Exit(1)

    def list_items(self):
        console.print(f"Available global {self.resource_type}s in [cyan]{self.global_dir}[/cyan]:")
        items = sorted([f.name for f in self.global_dir.glob(f"*{self.resource_ext}")])
        if not items:
            console.print(f"  No {self.resource_type}s found.")
            return
        for item in items:
            console.print(f"- {item}")
    
    def use(self, name: str):
        if not name.endswith(self.resource_ext):
            name += self.resource_ext
        source_path = self.global_dir / name
        if not source_path.exists():
            console.print(f"[bold red]Error:[/bold] {self.resource_type.capitalize()} '{name}' not found in the global library.")
            raise typer.Exit(1)

        project_paths = get_project_paths()
        dest_path = project_paths["resources"] / name
        try:
            shutil.copy(source_path, dest_path)
            console.print(f"[green]✓ Copied '{name}' to '{dest_path}'.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error copying file: {e}[/bold red]")
            raise typer.Exit(1)
        
        # 使用全新的、绝对可靠的 YAML 更新逻辑
        update_yaml_key(project_paths["metadata"], self.yaml_key, name)