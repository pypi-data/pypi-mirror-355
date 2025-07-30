# 存储 PAW 的核心配置和常量

from pathlib import Path

# PAW 全局资源库的根目录
PAW_HOME_DIR = Path.home() / ".paw"

# 全局 CSL 样式库存放目录
CSL_DIR = PAW_HOME_DIR / "csl"

# 全局 Word 模板库存放目录
TEMPLATES_DIR = PAW_HOME_DIR / "templates"