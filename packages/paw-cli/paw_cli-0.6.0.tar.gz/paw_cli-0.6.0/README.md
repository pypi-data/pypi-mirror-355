# **🐾 PAW: Pandoc Academic Workflow**

**PAW (Pandoc Academic Workflow)** 是一个为你量身打造的命令行工具，旨在提供一个一键式的、专业的、基于 Pandoc 和纯文本的学术写作环境。  
我们的愿景是，通过极致的自动化消除繁琐的技术配置，让你从写作的第一分钟起就专注于内容创作，同时享受版本控制、格式分离和高质量排版带来的所有优势。

## **✨ 核心功能**

- **一键式项目创建**: 使用 paw new 命令，瞬间生成一个包含标准目录结构、自动化编译脚本和预设配置文件的完整论文项目。
- **跨平台的内置编译**: 使用 paw build 命令，在任何操作系统上都能轻松将你的 Markdown 文稿编译成专业的 .pdf 和 .docx 格式文档，无需担心 make 的兼容性问题。
- **全局资源管理**: 通过 paw csl 和 paw template 命令，构建你自己的全局引文样式库和 Word 模板库，一次配置，所有项目共享。
- **无缝的引用体验**:
  - 使用 paw zotero (或 paw z)，一键唤出 Zotero 的文献选择器，告别手动导出 .bib 文件。
  - 使用 paw cite，快速在项目本地的 .bib 文件中搜索并插入引文。
- **高效的内容助手**: paw add chapter, paw add figure, paw add bib 等命令，让添加新章节、图片和参考文献变得轻而易举。
- **智能环境检查**: paw check 会自动检查你的电脑是否已安装 Pandoc 和 LaTeX 等核心依赖，并提供指引。
- **充满乐趣的彩蛋**: 我们在工具中埋下了一些有趣的彩蛋（试试 paw meow 或 paw woof），希望能为枯燥的学术写作带来一丝乐趣。

## **🚀 安装与使用**

### **1\. 前提条件**

在安装 PAW 之前，请确保你的电脑上已经安装了以下三个核心软件：

1. **Python** (版本 3.8 或更高)
2. **Pandoc**: PAW 的核心排版引擎。
3. **LaTeX 发行版**: 用于生成高质量的 PDF。
   - **macOS**: [MacTeX](https://www.tug.org/mactex/)
   - **Windows**: [MiKTeX](https://miktex.org/)
   - **Linux**: TeX Live (通常通过你的包管理器安装，如 sudo apt-get install texlive-full)

安装完成后，你可以随时运行 paw check 来确认这些依赖是否都已准备就绪。

### **2\. 安装 PAW**

我们**强烈推荐**使用 pipx 来安装 PAW，这可以确保它的运行环境与你的其他 Python 项目完全隔离。  
pipx install paw-cli

_(注意：在我们将 PAW 发布到 PyPI 之前，你可以暂时使用 pipx install . 在本地项目目录中安装)_  
当然，你也可以使用 pip 进行安装：  
pip install paw-cli

### **3\. 快速开始**

开启你的第一次 PAW 写作之旅：

1. **创建你的第一个项目**:  
   paw new "我的第一篇 PAW 论文"

2. **进入项目目录**:  
   cd 我的第一篇 paw 论文

3. **在 manuscript 文件夹中开始写作**。当你需要插入引文时：  
   \# 唤出 Zotero 选择器, 选择文献后, 引用键会自动复制到你的剪贴板  
   paw z

4. **编译你的论文**:  
   \# 这会同时生成 paper.pdf 和 paper.docx 在 output/ 文件夹中  
   paw build

## **📚 命令参考**

### **项目与环境**

- paw new "标题": 创建一个新项目。
  - 别名: paw chuangjian
- paw build: 编译项目，生成所有格式的文档。
  - \--pdf / \--no-pdf: 控制是否生成 PDF。
  - \--docx / \--no-docx: 控制是否生成 DOCX。
  - 别名: paw b
- paw check: 检查核心依赖。
  - 别名: paw c, paw jiancha, paw dig
- paw shake: 清理 output/ 输出目录。

### **内容添加**

- paw add chapter "标题": 添加一个新章节。
  - 别名: paw add chap, paw add zhang
- paw add figure \<路径\>: 添加一张图片。
  - \-c, \--caption "标题": 为图片添加标题。
  - 别名: paw add fig, paw add tupian
- paw add bib \<路径\>: 向项目中添加一个 .bib 参考文献文件。
  - 别名: paw add wenxian

### **引用管理**

- paw zotero: 触发 Zotero 的 CAYW 搜索框。
  - 别名: paw z
- paw cite \[关键词\]: 搜索项目本地 .bib 文件中的文献。
  - 别名: paw yinyong, paw hunt

### **资源库管理 (csl 和 template)**

- paw csl list: 列出全局库中所有可用的 CSL 样式。
- paw csl add \<路径\>: 向全局库中添加一个新的 CSL 文件。
- paw csl remove \<文件名\>: 从全局库中移除一个 CSL 文件。
- paw csl use \<文件名\>: 在当前项目中使用一个全局 CSL 文件。
- _template 命令与 csl 完全相同，只需将 csl 替换为 template 即可。_
  - 别名: style, yangshi (for csl), tmpl, moban (for template)

### **趣味彩蛋**

- paw meow: 获取一条随机的写作小贴士。
- paw woof: 查看当前项目的统计信息。
- paw purr: 以“满足的呼噜声”模式检查项目健康状态。
- paw paw (或 paw 🐾): 展示 PAW 的爪印。
- paw who-is-a-good-writer: 猜猜看？

## **许可证**

本项目基于 MIT 许可证分发。详情请见 LICENSE 文件。
