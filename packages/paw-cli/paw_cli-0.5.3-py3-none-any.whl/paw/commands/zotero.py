import typer
import requests
from rich.console import Console
import pyperclip

console = Console()

# Zotero Better BibTeX Cite-As-You-Write URL
BBT_CAYW_URL = "http://127.0.0.1:23119/better-bibtex/cayw"

def zotero():
    """
    触发 Zotero 的 "Cite-As-You-Write" 搜索框, 并将结果复制到剪贴板。
    
    需要 Zotero 正在运行, 并且已安装 Better BibTeX 插件。
    """
    # 参数确保我们获取带方括号的 Pandoc 格式引文
    params = {"format": "pandoc", "brackets": "true"}
    
    console.print(" aiting for you to pick a citation from Zotero...")
    try:
        # 移除 timeout, 让请求一直等待直到用户完成选择
        response = requests.get(BBT_CAYW_URL, params=params)
        response.raise_for_status() # 确保请求成功 (HTTP 200)
        
        citation = response.text
        if not citation:
            console.print("[yellow]Warning:[/yellow] No citation was selected in Zotero.")
            raise typer.Exit()

        # 将返回的引文复制到剪贴板
        pyperclip.copy(citation)
        console.print(f"\nCopied to clipboard: [bold cyan]{citation}[/bold cyan]")

    except requests.exceptions.ConnectionError:
        console.print("[bold red]Connection Error:[/bold red] Could not connect to Zotero.")
        console.print("Please ensure Zotero is running and the 'Better BibTeX' extension is installed.")
        raise typer.Exit(1)
        
    except pyperclip.PyperclipException:
        console.print("[bold red]Clipboard error:[/bold red] Could not copy to clipboard.")
        if 'citation' in locals():
             console.print(f"You can manually copy: [bold cyan]{citation}[/bold cyan]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        raise typer.Exit(1)
