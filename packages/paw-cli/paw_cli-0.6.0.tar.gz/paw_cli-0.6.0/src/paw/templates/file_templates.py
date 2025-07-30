# 包含所有项目模板文件内容的模块

import textwrap

def get_metadata_template(title: str) -> str:
    """
    (最终版) 生成一个独立的 metadata.yaml 文件。
    这个方案将配置与内容彻底分离，保证了稳定性。
    """
    return textwrap.dedent(f'''\
        # ======================================================================
        # PAW (Pandoc Academic Workflow) - Metadata File
        # ======================================================================
        # 
        # 这是项目的核心配置文件。PAW 会在编译时读取此文件。

        # --- 核心元数据 ---
        title: "{title}"
        author: 
          - 你的名字
        date: today # `today` 会自动替换为当前日期
        abstract: |  # 使用 `|` 来支持多行文本
          在这里撰写你的论文摘要。
          摘要内容可以跨越多行。
        keywords: ["关键词1", "关键词2", "关键词3"]

        # --- 章节与目录 ---
        toc: true
        toc-title: "目录"
        
        # --- 章节文件控制 (高级功能) ---
        # 默认情况下, PAW 会自动编译 manuscript/ 文件夹下所有 `数字-` 开头的 .md 文件。
        # 如果你想精确控制编译哪些章节, 可以取消下方 `input-files` 的注释。
        # 注意：这里的路径是相对于项目根目录的。摘要 (abstract) 是元数据，不应包含在此列表中。
        # input-files:
        #   - manuscript/01-introduction.md
        #   # - manuscript/02-draft-chapter.md # <-- 像这样注释掉即可排除

        # --- 本地化与标题 ---
        lang: "zh-CN"
        abstract-title: "摘要" # Pandoc 会为 abstract 内容自动添加标题
        reference-section-title: "参考文献"
        
        # --- 引用与文献 ---
        csl: "law-citation-manual.csl"
        bibliography: 
          - resources/bibliography.bib
        link-citations: true

        # --- 交叉引用与链接 ---
        figPrefix: "图"
        tblPrefix: "表"
        eqPrefix: "公式"
        link-crossrefs: true
        link-bibliography: true
        
        # --- 格式与字体 ---
        fontsize: 12pt
        geometry:
          - "top=3cm, bottom=3cm, left=2.5cm, right=2.5cm"
        mainfont: "Times New Roman"
        monofont: "Courier New"
        CJKmainfont: "Songti SC"
        CJKmonofont: "Heiti SC"

        # --- Word 文档模板 ---
        # reference-doc: your-template.docx
        
        # --- PDF 渲染引擎 ---
        pdf-engine: xelatex
    ''')


def get_introduction_template() -> str:
    return textwrap.dedent('''
        # 引言

        在这里开始你的第一章。
    ''').strip()


def get_makefile_template() -> str:
    # 最终版的 Makefile, 使用 --metadata-file, 更健壮
    return textwrap.dedent('''
        # ==============================================================================
        # PAW (Pandoc Academic Workflow) 生成的 Makefile - v1.0 (Final)
        # ==============================================================================
        
        # --- 基本配置 ---
        DOC_NAME = paper
        SRC_DIR = manuscript
        OUT_DIR = output
        RES_DIR = resources
        METADATA_FILE = $(SRC_DIR)/metadata.yaml

        # --- 智能章节检测 ---
        CHAPTERS_FROM_YAML := $(shell awk '/^input-files:/,/^[^ ]/ {{if ($$0 ~ /^-/) print $$2}}' $(METADATA_FILE))

        ifeq ($(strip $(CHAPTERS_FROM_YAML)),)
        	CHAPTER_FILES := $(shell find $(SRC_DIR) -name '[0-9]*.md' | sort)
        else
            CHAPTER_FILES := $(CHAPTERS_FROM_YAML)
        endif

        # --- Pandoc 配置 ---
        PANDOC = pandoc
        # 关键修复：将资源路径重新加入编译参数
        PANDOC_RESOURCE_PATHS = --resource-path=.:$(RES_DIR):$(HOME)/.paw/csl:$(HOME)/.paw/templates
        PANDOC_METADATA = --metadata-file=$(METADATA_FILE)
        PANDOC_FILTERS = -F pandoc-crossref
        PANDOC_CITEPROC = --citeproc
        
        PANDOC_FLAGS = $(PANDOC_RESOURCE_PATHS) $(PANDOC_METADATA) $(PANDOC_FILTERS) $(PANDOC_CITEPROC)

        # --- 目标定义 ---
        .PHONY: all pdf docx clean

        all: pdf docx

        pdf: $(OUT_DIR)/$(DOC_NAME).pdf
        docx: $(OUT_DIR)/$(DOC_NAME).docx

        # --- 编译规则 ---
        $(OUT_DIR):
        	@mkdir -p $(OUT_DIR)

        $(OUT_DIR)/$(DOC_NAME).pdf: $(CHAPTER_FILES) $(METADATA_FILE) | $(OUT_DIR)
        	@echo " brewing PDF..."
        	@$(PANDOC) $(PANDOC_FLAGS) -o $@ $(CHAPTER_FILES)
        	@echo "✅ Successfully created $@"

        $(OUT_DIR)/$(DOC_NAME).docx: $(CHAPTER_FILES) $(METADATA_FILE) | $(OUT_DIR)
        	@echo " baking DOCX..."
        	@$(PANDOC) $(PANDOC_FLAGS) -o $@ $(CHAPTER_FILES)
        	@echo "✅ Successfully created $@"

        clean:
        	@echo " cleaning output directory..."
        	@rm -rf $(OUT_DIR)/*
    ''')

def get_gitignore_template() -> str:
    # (已恢复完整内容)
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
    # (已恢复完整内容)
    return textwrap.dedent(f'''
        # {project_name}

        本项目由 PAW (Pandoc Academic Workflow) 创建。

        ## 快速开始

        1.  **编辑配置**: 打开 `manuscript/metadata.yaml` 文件，修改你的论文标题、作者等信息。
        2.  **开始写作**: 在 `manuscript/` 文件夹中编写你的 Markdown 文件，例如 `01-introduction.md`。
        3.  **插入引文**: 运行 `paw z` 唤出 Zotero 选择器。
        4.  **编译文档**: 在项目根目录下，运行 `paw build`。

        ## 核心工作流

        ### 章节管理

        PAW 提供两种模式来管理你的章节：

        1.  **自动模式 (默认)**
            -   `paw build` 命令会自动按数字顺序找到并编译 `manuscript/` 目录下的所有 `.md` 文件。

        2.  **手动模式 (高级)**
            -   打开 `manuscript/metadata.yaml` 文件。
            -   找到被注释掉的 `input-files` 列表。
            -   取消注释，并手动指定你想要编译的文件列表。

        ### 编译命令

        - `paw build`: (推荐) 同时生成 PDF 和 DOCX 格式的文档。
        - `paw build pdf`: 仅生成 PDF 文档。
        - `paw build docx`: 仅生成 DOCX 文档。
        - `paw shake`: 清理 `output/` 目录下的所有文件。

        祝你写作顺利！
    ''').strip()

def get_abstract_template() -> str:
    """为独立的摘要文件生成模板"""
    # 这个函数在最终方案中不再使用，但为了避免错误，我们保留它并返回一个提示
    return "# DEPRECATED: Abstract is now defined inside manuscript/metadata.yaml"
