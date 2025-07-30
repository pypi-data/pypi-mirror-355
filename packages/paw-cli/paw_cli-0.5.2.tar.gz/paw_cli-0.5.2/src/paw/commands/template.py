import typer
from pathlib import Path
from .. import config
from ..utils import ResourceHandler

app = typer.Typer(
    name="template",
    help="管理全局 Word (.docx) 模板文件。",
    no_args_is_help=True
)

handler = ResourceHandler(
    resource_type="template",
    resource_ext=".docx",
    global_dir=config.TEMPLATES_DIR,
    yaml_key="reference-doc"
)

@app.command("add", help="添加一个 Word 模板到全局库。")
def add_template(source_path: Path = typer.Argument(..., help="要添加的 .docx 文件的路径。", exists=True, file_okay=True, dir_okay=False, readable=True)):
    handler.add(source_path)

@app.command("remove", help="从全局库移除一个 Word 模板。")
def remove_template(name: str = typer.Argument(..., help="要移除的 Word 模板文件名 (例如 'my-template.docx')。")):
    handler.remove(name)

@app.command("list", help="列出所有可用的全局 Word 模板。")
def list_templates():
    handler.list_items()

@app.command("use", help="在当前项目中使用一个全局 Word 模板。")
def use_template(name: str = typer.Argument(..., help="要使用的 Word 模板文件名 (例如 'my-template.docx')。")):
    handler.use(name)