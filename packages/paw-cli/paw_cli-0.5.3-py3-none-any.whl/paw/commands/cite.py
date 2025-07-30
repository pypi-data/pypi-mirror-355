import typer
from rich.console import Console
from rich.prompt import Prompt
import pyperclip
from pybtex.database import parse_file as parse_bib_file, BibliographyData, Entry
from .. import utils

console = Console()

def format_entry(entry: Entry) -> str:
    """格式化文献条目以便在列表中显示"""
    authors = "Unknown Author"
    if 'author' in entry.persons:
        # 将作者列表格式化，例如 "A, B and C"
        author_list = [str(p) for p in entry.persons['author']]
        if len(author_list) > 2:
            authors = f"{', '.join(author_list[:-1])}, and {author_list[-1]}"
        else:
            authors = ' and '.join(author_list)

    year = entry.fields.get('year', 'N/A')
    title = entry.fields.get('title', 'No Title')
    # 缩短过长的标题
    if len(title) > 60:
        title = title[:57] + "..."
        
    return f"[yellow]{entry.key}[/yellow] - {authors} ({year}). {title}"

def cite(keywords: list[str] = typer.Argument(None, help="用于搜索文献的关键词 (作者, 年份, 标题等)。")):
    """
    交互式搜索参考文献并复制引用键。
    """
    project_paths = utils.get_project_paths()

    # 从 YAML 获取所有 .bib 文件路径
    try:
        with open(project_paths["frontmatter"], 'r', encoding='utf-8') as f:
            docs = list(utils.yaml.load_all(f))
        bib_paths_config = docs[0].get("bibliography", [])
        if isinstance(bib_paths_config, str):
            bib_paths_config = [bib_paths_config]
    except Exception as e:
        console.print(f"[bold red]Error reading bibliography from frontmatter: {e}[/bold red]")
        raise typer.Exit(1)

    if not bib_paths_config:
        console.print("[bold yellow]Warning:[/bold yellow] No 'bibliography' key found in frontmatter. Cannot search for citations.")
        raise typer.Exit()

    # 加载所有文献条目
    all_entries = {}
    for bib_path_str in bib_paths_config:
        bib_path = project_paths["root"] / bib_path_str
        if not bib_path.exists():
            console.print(f"[bold yellow]Warning:[/bold yellow] Bibliography file not found: {bib_path}")
            continue
        try:
            bib_data = parse_bib_file(str(bib_path), 'bibtex')
            all_entries.update(bib_data.entries)
        except Exception as e:
            console.print(f"[bold red]Error parsing bib file {bib_path}: {e}[/bold red]")

    if not all_entries:
        console.print("[bold red]Error:[/bold red] No citation entries found in any .bib file.")
        raise typer.Exit(1)
    
    # 搜索文献
    if not keywords:
        console.print("No keywords provided. Listing all citations...")
        found_entries = list(all_entries.values())
    else:
        search_terms = [k.lower() for k in keywords]
        found_entries = []
        for key, entry in all_entries.items():
            entry_text = str(entry.to_string('bibtex')).lower()
            if all(term in entry_text for term in search_terms):
                found_entries.append(entry)

    if not found_entries:
        console.print("No matching citations found.")
        raise typer.Exit()

    # 交互式选择
    console.print("\n[bold green]Found matching citations:[/bold green]")
    for i, entry in enumerate(found_entries):
        console.print(f"  [bold cyan]{i+1}[/bold cyan]: {format_entry(entry)}")

    choice = Prompt.ask("\nEnter the number of the citation to copy (or 'q' to quit)", default="1")
    
    if choice.lower() == 'q':
        console.print("Aborted.")
        raise typer.Exit()

    try:
        choice_idx = int(choice) - 1
        if not 0 <= choice_idx < len(found_entries):
            raise ValueError
        
        selected_key = found_entries[choice_idx].key
        citation_to_copy = f"[@{selected_key}]"
        
        pyperclip.copy(citation_to_copy)
        console.print(f"\nCopied to clipboard: [bold cyan]{citation_to_copy}[/bold cyan]")

    except (ValueError, IndexError):
        console.print("[bold red]Invalid selection.[/bold red]")
        raise typer.Exit(1)
    except pyperclip.PyperclipException as e:
        console.print(f"[bold red]Clipboard error:[/bold red] Could not copy to clipboard. Please install 'xclip' or 'xsel' on Linux, or check your system.")
        console.print(f"You can manually copy: [bold cyan]{citation_to_copy}[/bold cyan]")
