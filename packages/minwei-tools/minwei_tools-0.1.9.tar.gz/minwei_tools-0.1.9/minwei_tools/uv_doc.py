import os
from pathlib import Path
import textwrap

IGNORE_DIRS = {".venv", "__pycache__", ".git", ".mypy_cache", ".idea", "*.egg", "*.egg-info", "node_modules", ".vscode", ".pytest_cache", "dist"}

def get_project_name(path : Path):
    return path.name if path.is_dir() else path.parent.name

def build_tree(path: Path, prefix="") -> list[str]:
    lines = []
    entries = sorted([p for p in path.iterdir() if p.name not in IGNORE_DIRS])
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(build_tree(entry, prefix + extension))
    return lines

def generate_readme(project_name, tree_structure):
    return f"""\
# {project_name}

## 📁 專案結構範例

```
{project_name}/
{tree_structure}
```

---

## 🚀 安裝與啟動說明

此專案使用 [uv](https://github.com/astral-sh/uv) 來管理 Python 環境與套件。
以下是安裝與啟動的步驟：

### 1. 安裝 uv

如果已安裝 Rust，可透過 cargo 安裝：

```bash
cargo install uv
```

如果有基本的python跟pip

```bash
pip install uv
```

或使用官方安裝腳本：

```ps
curl -LsSf https://astral.sh/uv/install.sh | sh
```

如果是在 windows底下:
```ps
wget -qO- https://astral.sh/uv/install.sh | sh

```

---

### 1. 同步 `pyproject.toml` 

```bash
uv sync
```

---

### 3. 進入開發環境

```bash
source .venv/bin/activate   # 或使用 uv shell
```

### 4. 啟動專案
```bash
uv run main.py
```

"""


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Generate a README.md file for the current project.")
    parser.add_argument("-p", "--project_name", type=str, help="Name of the project. Defaults to the current directory name.")
    parser.add_argument("-o", "--output"      , type=str, default="README.md", help="Output file name. Defaults to README.md.")
    parser.add_argument("-d", "--directory"   , type=str, default=os.getcwd(), help="Directory to scan. Defaults to the current working directory.")
    args = parser.parse_args()

    project_path    = Path(args.directory).resolve() if args.directory else Path.cwd()

    project_name = args.project_name if args.project_name else None
    if not project_name:
        project_name    = get_project_name(project_path)

    output_filename = args.output
    output_filepath = Path(project_path) / output_filename
    
    # 獲取專案結構
    tree_lines = build_tree(project_path)
    tree       = "\n".join(tree_lines)
    
    # 生成 README 內容
    readme_content = generate_readme(project_name, tree)
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(readme_content))
    
    print(f"README.md 已生成於 {output_filepath}")
