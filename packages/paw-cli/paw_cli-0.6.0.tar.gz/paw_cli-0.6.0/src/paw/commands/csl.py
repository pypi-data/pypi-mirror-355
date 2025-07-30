import typer
from pathlib import Path
from .. import config
from ..utils import ResourceHandler

app = typer.Typer(
    name="csl",
    help="管理全局 CSL (Citation Style Language) 样式文件。",
    no_args_is_help=True
)

handler = ResourceHandler(
    resource_type="csl",
    resource_ext=".csl",
    global_dir=config.CSL_DIR,
    yaml_key="csl"
)

@app.command("add", help="添加一个 CSL 文件到全局库。")
def add_csl(source_path: Path = typer.Argument(..., help="要添加的 .csl 文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True)):
    handler.add(source_path)

@app.command("remove", help="从全局库移除一个 CSL 文件。")
def remove_csl(name: str = typer.Argument(..., help="要移除的 CSL 样式文件名 (例如 'apa.csl')。")):
    handler.remove(name)

@app.command("list", help="列出所有可用的全局 CSL 文件。")
def list_csl():
    handler.list_items()

@app.command("use", help="在当前项目中使用一个全局 CSL 文件。")
def use_csl(name: str = typer.Argument(..., help="要使用的 CSL 样式文件名 (例如 'apa.csl')。")):
    handler.use(name)