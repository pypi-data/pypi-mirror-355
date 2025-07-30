# 通用工具函数模块

import shutil
import re
import io
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

def read_frontmatter(file_path: Path) -> tuple[dict, str, str]:
    """
    读取 .md 文件，分离 YAML frontmatter 和文件的其余内容。
    返回 (YAML数据, YAML字符串, 文件其余部分字符串)。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        match = re.match(r'^---\s*\n(.*?\n)---\s*\n', text, re.DOTALL)
        if not match:
            return {}, "", text

        yaml_string = match.group(1)
        rest_of_file = text[match.end():]
        data = yaml.load(yaml_string)
        return data, yaml_string, rest_of_file
    except Exception as e:
        console.print(f"[bold red]Error reading frontmatter from {file_path}: {e}[/bold red]")
        raise typer.Exit(1)

def write_frontmatter(file_path: Path, data: dict, rest_of_file: str):
    """将 YAML 数据和文件其余部分写回文件，保留 --- 分隔符。"""
    try:
        string_stream = io.StringIO()
        yaml.dump(data, string_stream)
        yaml_string = string_stream.getvalue()

        # 确保文件以 `---` 开头和结尾
        full_content = f"---\n{yaml_string}---\n{rest_of_file}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
    except Exception as e:
        console.print(f"[bold red]Error writing frontmatter to {file_path}: {e}[/bold red]")
        raise typer.Exit(1)


def ensure_paw_dirs():
    """确保 PAW 全局资源目录存在"""
    try:
        config.PAW_HOME_DIR.mkdir(exist_ok=True)
        config.CSL_DIR.mkdir(exist_ok=True)
        config.TEMPLATES_DIR.mkdir(exist_ok=True)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold] Could not create PAW home directories in '{config.PAW_HOME_DIR}'.")
        console.print(f"Reason: {e}")
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
    """获取当前 PAW 项目的关键路径"""
    root = find_project_root()
    if not root:
        console.print("[bold red]Error:[/bold] Not inside a PAW project. Could not find project root.")
        raise typer.Exit(1)
    
    paths = {
        "root": root,
        "manuscript": root / "manuscript",
        "resources": root / "resources",
        "figures": root / "figures",
        "output": root / "output",
        "frontmatter": root / "manuscript" / "00-frontmatter.md"
    }
    if not paths["frontmatter"].exists():
        console.print(f"[bold red]Error:[/bold] Frontmatter file not found at '{paths['frontmatter']}'")
        raise typer.Exit(1)
    return paths


def update_yaml_list(yaml_path: Path, key: str, value: str):
    """智能地更新 YAML 文件中的一个键，保留文件结构。"""
    try:
        data, _, rest_of_file = read_frontmatter(yaml_path)
        if key not in data:
            data[key] = [value]
        else:
            current_value = data.get(key)
            if isinstance(current_value, str):
                if current_value != value:
                    data[key] = [current_value, value]
            elif isinstance(current_value, list):
                if value not in current_value:
                    current_value.append(value)
            else:
                 data[key] = [value]
        
        write_frontmatter(yaml_path, data, rest_of_file)
        console.print(f"[green]✓ Updated '{key}' in '{yaml_path.name}'.[/green]")

    except Exception as e:
        console.print(f"[bold red]Error updating YAML file: {e}[/bold red]")
        raise typer.Exit(1)


class ResourceHandler:
    """处理 CSL 和 Template 资源的通用逻辑类"""
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

        try:
            data, _, rest_of_file = read_frontmatter(project_paths["frontmatter"])
            data[self.yaml_key] = name
            write_frontmatter(project_paths["frontmatter"], data, rest_of_file)
            console.print(f"[green]✓ Updated '{self.yaml_key}' in '{project_paths['frontmatter'].name}'.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error updating YAML frontmatter: {e}[/bold red]")
            raise typer.Exit(1)
