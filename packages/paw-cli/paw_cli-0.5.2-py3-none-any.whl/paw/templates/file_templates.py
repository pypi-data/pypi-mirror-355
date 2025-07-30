# 包含所有项目模板文件内容的模块

import textwrap

def get_frontmatter_template(title: str) -> str:
    # 最终修正版的 frontmatter 模板, 修复了缩进问题
    # 使用 textwrap.dedent 来正确处理多行字符串的缩进
    return textwrap.dedent(f'''\
        ---
        # ======================================================================
        # PAW (Pandoc Academic Workflow) - YAML Frontmatter
        # ======================================================================
        
        # --- 核心元数据 ---
        title: "{title}"
        author: 
          - 你的名字
        date: today # `today` 会自动替换为当前日期
        abstract: |
          在这里撰写你的论文摘要。
          摘要内容可以跨越多行。
        keywords: ["关键词1", "关键词2", "关键词3"]

        # --- 章节与目录 ---
        toc: true
        toc-title: "目录"
        
        # --- 章节文件控制 (高级功能) ---
        # 默认情况下, PAW 会自动编译 manuscript/ 文件夹下所有 `数字-` 开头的 .md 文件。
        # 如果你想精确控制编译哪些章节 (例如, 暂时排除某个草稿章节),
        # 可以取消下方 `input-files` 的注释, 并手动指定文件列表。
        # input-files:
        #   - manuscript/01-introduction.md
        #   - manuscript/02-literature-review.md
        #   # - manuscript/03-draft-chapter.md # <-- 像这样注释掉即可排除
        #   - manuscript/04-methodology.md

        # --- 本地化与标题 ---
        lang: "zh-CN"
        abstract-title: "摘要"
        reference-section-title: "参考文献"
        
        # --- 引用与文献 ---
        csl: "law-citation-manual.csl" # 默认引用样式
        bibliography: 
          - resources/bibliography.bib # 默认文献库
        link-citations: true

        # --- 交叉引用与链接 ---
        # pandoc-crossref 的配置
        figPrefix: "图"
        tblPrefix: "表"
        eqPrefix: "公式"
        # 内部链接设置
        link-crossrefs: true
        link-bibliography: true # 在参考文献列表中为条目添加链接
        
        # --- 格式与字体 ---
        # 以下为推荐配置。请根据你的操作系统安装并选择合适的字体。
        # macOS 常见中文字体: Songti SC (宋体), Kaiti SC (楷体), Heiti SC (黑体)
        # Windows 常见中文字体: SimSun (宋体), SimHei (黑体), Kaiti (楷体)
        fontsize: 12pt
        geometry:
          - "top=3cm, bottom=3cm, left=2.5cm, right=2.5cm"
        mainfont: "Times New Roman"
        monofont: "Courier New"
        CJKmainfont: "Songti SC" # 默认使用 macOS 的宋体, Windows 用户请修改为 SimSun
        CJKmonofont: "Heiti SC" # 默认使用 macOS 的黑体, Windows 用户请修改为 SimHei

        # --- Word 文档模板 ---
        # 可通过 `paw template use <模板名>` 命令来设置
        # reference-doc: your-template.docx
        
        # --- PDF 渲染引擎 ---
        # 推荐使用 xelatex 以获得最佳的中文支持
        pdf-engine: xelatex
        ---
        
        <!-- 
        此文件用于定义整篇论文的元数据。
        Pandoc 会在编译时读取这些配置。
        正文内容请在 01-introduction.md 等文件中编写。
        -->
    ''')


def get_introduction_template() -> str:
    return textwrap.dedent('''
        # 引言

        在这里开始你的第一章。
    ''').strip()


def get_gitignore_template() -> str:
    return textwrap.dedent('''
        # PAW 生成的 .gitignore

        # 忽略编译输出目录
        /output/

        # Python 缓存与临时文件
        __pycache__/
        *.py[cod]
        *$py.class

        # Python 构建与安装产物
        *.egg-info/
        src/*.egg-info/
        build/
        dist/
        
        # 虚拟环境目录
        .venv/
        venv/
        ENV/

        # 编辑器与系统文件
        .vscode/
        .idea/
        .DS_Store
        *.swp
        
        # PAW 全局资源库 (不应在项目内)
        .paw/
    ''').strip()


def get_readme_template(project_name: str) -> str:
    # 更新 README 以推荐使用 paw build 命令
    return textwrap.dedent(f'''
        # {project_name}

        本项目由 PAW (Pandoc Academic Workflow) 创建。

        ## 快速开始

        1.  **编写内容**: 在 `manuscript/` 文件夹中编写你的 Markdown 文件。文件名以 `数字-` 开头以确保编译顺序。
        2.  **管理资源**:
            - 使用 `paw csl add <样式文件.csl>` 将你常用的 CSL 文件添加到全局库。
            - 运行 `paw zotero` (或 `paw z`) 调出选择器，插入引文。
        3.  **编译文档**: 在项目根目录下，打开终端，运行 `paw build`。

        ## 核心工作流

        ### 章节管理

        PAW 提供两种模式来管理你的章节：

        1.  **自动模式 (默认)**
            -   你只需在 `manuscript/` 目录下创建以 `数字-` 开头的文件 (例如 `01-introduction.md`)。
            -   `paw build` 命令会自动按顺序找到并编译所有这些文件。

        2.  **手动模式 (高级)**
            -   打开 `manuscript/00-frontmatter.md` 文件。
            -   找到被注释掉的 `input-files` 列表。
            -   取消注释，并手动指定你想要编译的文件列表。这对于临时排除草稿章节非常有用。

        ### 编译命令

        - `paw build`: (推荐) 同时生成 PDF 和 DOCX 格式的文档。
        - `paw build pdf`: 仅生成 PDF 文档。
        - `paw build docx`: 仅生成 DOCX 文档。
        - `paw shake`: 清理 `output/` 目录下的所有文件。

        祝你写作顺利！
    ''').strip()


def get_makefile_template() -> str:
    # 最终版的 Makefile, 实现了对 input-files 和 reference-doc 的智能判断
    return textwrap.dedent('''
        # ==============================================================================
        # PAW (Pandoc Academic Workflow) 生成的 Makefile - v1.0 (Final)
        # ==============================================================================
        #
        # 注意: Makefile 仅为熟悉 make 的用户提供便利。
        # 推荐使用跨平台的 `paw build` 命令来编译项目。
        
        # --- 基本配置 ---
        DOC_NAME = paper
        SRC_DIR = manuscript
        OUT_DIR = output
        RES_DIR = resources
        FRONTMATTER = $(SRC_DIR)/00-frontmatter.md

        # --- 智能章节检测 ---
        INPUT_FILES_FROM_YAML := $(shell awk '/^input-files:/,/^[^ ]|---$$/ {{if ($$0 ~ /^-/) print $$2}}' $(FRONTMATTER))

        ifeq ($(strip $(INPUT_FILES_FROM_YAML)),)
        	CHAPTERS := $(shell find $(SRC_DIR) -name '[0-9]*.md' | sort)
        else
        	CHAPTERS := $(INPUT_FILES_FROM_YAML)
        endif

        # --- Pandoc 配置 ---
        PANDOC = pandoc
        PANDOC_RESOURCE_PATHS = --resource-path=.:$(RES_DIR):$(HOME)/.paw/csl:$(HOME)/.paw/templates
        PANDOC_FILTERS = -F pandoc-crossref
        PANDOC_CITEPROC = --citeproc
        PDF_ENGINE = --pdf-engine=xelatex
        
        # --- DOCX 模板智能检测 ---
        # 从 YAML frontmatter 中直接读取 reference-doc 的值, Pandoc 会利用 resource-path 自动查找
        WORD_TEMPLATE_FILE := $(shell awk '/^reference-doc:/ {{$$1=""; print $$0}}' $(FRONTMATTER) | xargs)
        WORD_TEMPLATE_FLAG := $(if $(WORD_TEMPLATE_FILE),--reference-doc="$(WORD_TEMPLATE_FILE)",)
        
        PANDOC_FLAGS = $(PANDOC_RESOURCE_PATHS) $(PANDOC_FILTERS) $(PANDOC_CITEPROC)

        # --- 目标定义 ---
        .PHONY: all pdf docx clean

        all: pdf docx

        pdf: $(OUT_DIR)/$(DOC_NAME).pdf
        docx: $(OUT_DIR)/$(DOC_NAME).docx

        # --- 编译规则 ---
        $(OUT_DIR):
        	@mkdir -p $(OUT_DIR)

        $(OUT_DIR)/$(DOC_NAME).pdf: $(CHAPTERS) | $(OUT_DIR)
        	@echo " brewing PDF..."
        	@$(PANDOC) $(PANDOC_FLAGS) $(PDF_ENGINE) -o $@ $(CHAPTERS)
        	@echo "✅ Successfully created $@"

        $(OUT_DIR)/$(DOC_NAME).docx: $(CHAPTERS) | $(OUT_DIR)
        	@echo " baking DOCX..."
        	@$(PANDOC) $(PANDOC_FLAGS) $(WORD_TEMPLATE_FLAG) -o $@ $(CHAPTERS)
        	@echo "✅ Successfully created $@"

        clean:
        	@echo " cleaning output directory..."
        	@rm -rf $(OUT_DIR)/*
    ''').strip()
