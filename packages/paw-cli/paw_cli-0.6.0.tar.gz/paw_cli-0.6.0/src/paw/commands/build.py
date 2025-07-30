import typer
import subprocess
import re
from typing import Optional
from rich.console import Console
from .. import utils
from pathlib import Path

console = Console()

def get_chapters(project_paths):
    """根据 input-files 逻辑决定章节列表"""
    metadata_path = project_paths["metadata"]
    try:
        data = utils.read_yaml_file(metadata_path)
        input_files = data.get("input-files")
        
        if input_files and isinstance(input_files, list):
            manual_chapters = [str(project_paths["root"] / file) for file in input_files]
            return manual_chapters
    except Exception:
        pass

    auto_chapters = sorted(project_paths["manuscript"].glob("[0-9]*.md"))
    return [str(p) for p in auto_chapters]


def run_pandoc(output_format: str, project_paths):
    """运行 Pandoc 命令的核心逻辑 (最终版)"""
    console.print(f" brewing [bold blue]{output_format.upper()}[/bold blue]...")
    
    output_dir = project_paths["output"]
    output_dir.mkdir(exist_ok=True)
    
    doc_name = "paper"
    output_path = output_dir / f"{doc_name}.{output_format}"
    
    chapters = get_chapters(project_paths)
    if not chapters:
        console.print("[bold red]Error:[/bold red] No chapter files found.")
        raise typer.Exit(1)
        
    pandoc_exec = utils.get_pandoc_path()

    # (最终版) 这是最可靠的构建方式
    command = [
        pandoc_exec,
        f"--resource-path={project_paths['root']}:{project_paths['resources']}:{utils.config.CSL_DIR}:{utils.config.TEMPLATES_DIR}",
        "--metadata-file", str(project_paths["metadata"]),
        "-F", "pandoc-crossref",
        "--citeproc",
    ]

    # --- 关键修复：从 metadata.yaml 读取并应用模板和PDF引擎 ---
    try:
        data = utils.read_yaml_file(project_paths["metadata"])
        if output_format == "docx":
            template_file = data.get("reference-doc")
            if template_file:
                # Pandoc会利用resource-path自动寻找,我们只需提供文件名或相对/绝对路径
                command.extend(["--reference-doc", template_file])
        
        if output_format == "pdf":
            pdf_engine = data.get("pdf-engine", "xelatex")
            command.extend([f"--pdf-engine={pdf_engine}"])
    except Exception:
        # 如果 YAML 解析失败, 使用默认的 pdf-engine
        if output_format == "pdf":
             command.extend(["--pdf-engine=xelatex"])
    # --- 修复结束 ---

    command.extend(["-o", str(output_path)])
    command.extend(chapters)

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        if result.stderr:
            warnings = [line for line in result.stderr.splitlines() if "warning" in line.lower()]
            if warnings:
                console.print("[yellow]Pandoc Warnings:[/yellow]")
                for warning in warnings:
                    console.print(f"  {warning}")
        console.print(f"✅ [bold green]Successfully created {output_path}[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Pandoc Error (Exit Code {e.returncode}):[/bold red]")
        console.print(e.stderr)
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] '{pandoc_exec}' command not found. Please run 'paw check'.")
        raise typer.Exit(1)

def build(
    pdf: Optional[bool] = typer.Option(None, "--pdf", help="仅编译 PDF。"),
    docx: Optional[bool] = typer.Option(None, "--docx", help="仅编译 DOCX。")
):
    """
    编译项目, 生成最终文档。
    默认行为 (不带任何标志): 同时编译 PDF 和 DOCX。
    """
    project_paths = utils.get_project_paths()

    # 显式模式：如果用户指定了 --pdf 或 --docx
    if pdf is True or docx is True:
        if pdf:
            run_pandoc("pdf", project_paths)
        if docx:
            run_pandoc("docx", project_paths)
    # 默认模式：如果用户只输入 `paw build`
    else:
        run_pandoc("pdf", project_paths)
        run_pandoc("docx", project_paths)
