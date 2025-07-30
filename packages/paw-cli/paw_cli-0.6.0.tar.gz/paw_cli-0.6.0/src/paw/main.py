import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated")

import typer
from .commands import (
    new as new_cmd,
    check as check_cmd,
    csl as csl_cmd,
    template as template_cmd,
    add as add_cmd,
    cite as cite_cmd,
    zotero as zotero_cmd,
    easter_eggs as easter_eggs_cmd,
    shake as shake_cmd,
    build as build_cmd,
)

app = typer.Typer(
    name="paw",
    help="🐾 PAW: Your loyal academic companion. Let me lend a paw!",
    add_completion=False,
    no_args_is_help=True,
)

# --- 核心功能命令 ---
app.command(name="new", help="创建一个新的 PAW 学术项目。")(new_cmd.new)
app.command(name="chuangjian", help='Alias for "new".', hidden=True)(new_cmd.new)

app.command(name="check", help="检查核心依赖 (Pandoc, LaTeX)。")(check_cmd.check)
app.command(name="c", help='Alias for "check".', hidden=True)(check_cmd.check)
app.command(name="jiancha", help='Alias for "check".', hidden=True)(check_cmd.check)
app.command(name="dig", help="深入诊断项目依赖。 Alias for 'check'.")(check_cmd.check)
app.command(name="purr", help="检查项目健康状态 (如果一切正常会发出呼噜声)。")(check_cmd.check_purr)

# --- 编译命令 (推荐) ---
app.command(name="build", help="编译项目, 生成最终文档。")(build_cmd.build)
app.command(name="b", help='Alias for "build".', hidden=True)(build_cmd.build)


# --- 内容管理命令组 ---
app.add_typer(add_cmd.app, name="add")

# --- 引用命令 ---
app.command(name="cite", help="交互式搜索本地 .bib 文件并复制引用键。")(cite_cmd.cite)
app.command(name="yinyong", help='Alias for "cite".', hidden=True)(cite_cmd.cite)
app.command(name="hunt", help="搜寻本地文献。 Alias for 'cite'.")(cite_cmd.cite)

app.command(name="zotero", help='触发 Zotero CAYW 搜索框。 Alias: "z".')(zotero_cmd.zotero)
app.command(name="z", help='Alias for "zotero".', hidden=True)(zotero_cmd.zotero)


# --- 资源管理命令组 ---
app.add_typer(csl_cmd.app, name="csl")
app.add_typer(csl_cmd.app, name="style", help='Alias for "csl".', hidden=True)
app.add_typer(csl_cmd.app, name="yangshi", help='Alias for "csl".', hidden=True)

app.add_typer(template_cmd.app, name="template")
app.add_typer(template_cmd.app, name="tmpl", help='Alias for "template".', hidden=True)
app.add_typer(template_cmd.app, name="moban", help='Alias for "template".', hidden=True)


# --- 趣味性与实用工具 ---
app.command(name="shake", help="清理输出目录 (像狗狗甩水一样)。")(shake_cmd.shake)
app.command(name="meow", help="显示一条随机的学术写作小贴士。")(easter_eggs_cmd.meow)
app.command(name="woof", help="快速汇报项目统计信息。")(easter_eggs_cmd.woof)


# --- 隐藏彩蛋 ---
app.command(name="paw", hidden=True)(easter_eggs_cmd.show_paw)
app.command(name="🐾", help='Alias for "paw".', hidden=True)(easter_eggs_cmd.show_paw)
app.command(name="who-is-a-good-writer", hidden=True)(easter_eggs_cmd.praise)

# 添加一个 main 函数以适配可能的未来扩展
def main():
    app()

if __name__ == "__main__":
    main()
