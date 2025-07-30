import typer
import subprocess
import re
from rich.console import Console
from .. import utils

console = Console()

def get_chapters(project_paths):
    """根据 input-files 逻辑决定章节列表"""
    frontmatter_path = project_paths["frontmatter"]
    try:
        with open(frontmatter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        input_files_match = re.search(r"^input-files:\s*\n((?:\s*-\s*.*\n)+)", content, re.MULTILINE)
        
        if input_files_match:
            files_str = input_files_match.group(1)
            files = [line.strip()[2:].strip() for line in files_str.strip().split('\n')]
            manual_chapters = [str(project_paths["root"] / file) for file in files]
            is_frontmatter_present = any(frontmatter_path.samefile(Path(p)) for p in manual_chapters)
            if not is_frontmatter_present:
                 manual_chapters.insert(0, str(frontmatter_path))
            return manual_chapters
    except Exception:
        pass

    auto_chapters = sorted(project_paths["manuscript"].glob("[0-9]*.md"))
    return [str(p) for p in auto_chapters]


def run_pandoc(output_format: str, project_paths):
    """运行 Pandoc 命令的核心逻辑"""
    console.print(f" brewing [bold blue]{output_format.upper()}[/bold blue]...")
    
    output_dir = project_paths["output"]
    output_dir.mkdir(exist_ok=True)
    
    doc_name = "paper"
    output_path = output_dir / f"{doc_name}.{output_format}"
    
    chapters = get_chapters(project_paths)
    if not chapters:
        console.print("[bold red]Error:[/bold red] No chapter files found.")
        raise typer.Exit(1)

    command = [
        "pandoc",
        f"--resource-path={project_paths['root']}:{project_paths['resources']}:{utils.config.CSL_DIR}:{utils.config.TEMPLATES_DIR}",
        "-F", "pandoc-crossref",
        "--citeproc",
    ]
    
    try:
        data, _, _ = utils.read_frontmatter(project_paths["frontmatter"])
        if output_format == "docx":
            template_file = data.get("reference-doc")
            if template_file:
                command.extend(["--reference-doc", template_file])
        
        if output_format == "pdf":
            pdf_engine = data.get("pdf-engine", "xelatex")
            command.extend([f"--pdf-engine={pdf_engine}"])
    except Exception:
        if output_format == "pdf":
             command.extend(["--pdf-engine=xelatex"])
    
    command.extend(["-o", str(output_path)])
    command.extend(chapters)

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        if result.stderr:
            console.print("[yellow]Pandoc Warnings:[/yellow]")
            console.print(result.stderr)
        console.print(f"✅ [bold green]Successfully created {output_path}[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Pandoc Error (Exit Code {e.returncode}):[/bold red]")
        console.print(e.stderr)
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[bold red]Error:[/bold red] 'pandoc' command not found. Please run 'paw check'.")
        raise typer.Exit(1)

from typing import Optional

def build(
    pdf: Optional[bool] = typer.Option(None, "--pdf/--no-pdf", help="编译 PDF。"),
    docx: Optional[bool] = typer.Option(None, "--docx/--no-docx", help="编译 DOCX。")
):
    """
    编译项目, 生成最终文档 (跨平台, 推荐使用)。
    默认同时编译 PDF 和 DOCX。
    如果明确指定 --pdf 或 --docx, 则只编译指定的格式。
    """
    project_paths = utils.get_project_paths()

    # 初始状态：假设用户没有提供任何选项，默认生成 PDF 和 DOCX
    build_pdf = True
    build_docx = True

    # 检查用户是否明确指定了任何一个选项
    pdf_explicitly_set = pdf is not None
    docx_explicitly_set = docx is not None

    if pdf_explicitly_set or docx_explicitly_set:
        # 如果用户明确指定了至少一个选项，则覆盖默认行为
        # 此时，只有被明确设置为 True 的才生成
        build_pdf = pdf if pdf_explicitly_set else False
        build_docx = docx if docx_explicitly_set else False
        
        # 针对用户只指定其中一个选项的情况进行修正
        if pdf_explicitly_set and not docx_explicitly_set:
            # 用户明确指定了 PDF 选项，但没有指定 DOCX 选项
            # 如果 pdf 是 False (即 --no-pdf)，那么只生成 DOCX
            if not pdf:
                build_docx = True
            # 如果 pdf 是 True (即 --pdf)，那么不生成 DOCX
            else:
                build_docx = False
        elif docx_explicitly_set and not pdf_explicitly_set:
            # 用户明确指定了 DOCX 选项，但没有指定 PDF 选项
            # 如果 docx 是 False (即 --no-docx)，那么只生成 PDF
            if not docx:
                build_pdf = True
            # 如果 docx 是 True (即 --docx)，那么不生成 PDF
            else:
                build_pdf = False

    if not build_pdf and not build_docx:
        console.print("Nothing to build. Use --pdf or --docx flags, or run without flags to build both.")
        return

    if build_pdf:
        run_pandoc("pdf", project_paths)
    if build_docx:
        run_pandoc("docx", project_paths)
