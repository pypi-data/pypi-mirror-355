import os
import sys
import argparse
from pathlib import Path


def create_project_structure(project_dir: str) -> None:
    """创建项目的基本目录结构"""
    # 定义需要创建的目录
    directories = [
        f"{project_dir}/src",
        f"{project_dir}/tests",
        f"{project_dir}/docs",
        f"{project_dir}/scripts",
        f"{project_dir}/data",
        f"{project_dir}/models",
        f"{project_dir}/reports"
    ]

    # 创建主项目目录
    try:
        os.makedirs(project_dir, exist_ok=True)
        print(f"创建项目目录: {project_dir}")
    except OSError as e:
        print(f"无法创建项目目录: {e}", file=sys.stderr)
        sys.exit(1)

    # 创建子目录
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")
        except OSError as e:
            print(f"无法创建目录 {directory}: {e}", file=sys.stderr)

    # 创建初始文件
    create_initial_files(project_dir)


def create_initial_files(project_dir: str) -> None:
    """创建项目的初始文件"""
    files = {
        f"{project_dir}/README.md": "# 项目文档\n这是项目的文档说明",
        f"{project_dir}/.gitignore": "# 忽略常见文件\n__pycache__/\n*.pyc\n*.pyo\n*.pyd\n",
        f"{project_dir}/requirements.txt": "# 项目依赖\n",
        f"{project_dir}/src/__init__.py": "",
        f"{project_dir}/tests/__init__.py": ""
    }

    for file_path, content in files.items():
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"创建文件: {file_path}")
        except OSError as e:
            print(f"无法创建文件 {file_path}: {e}", file=sys.stderr)


def main() -> None:
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        prog="lorien",
        description="Lorien 项目初始化工具"
    )

    subparsers = parser.add_subparsers(dest="command")

    # 创建 init 子命令
    init_parser = subparsers.add_parser("init", help="初始化新项目")
    init_parser.add_argument("project_name", help="项目名称")
    init_parser.add_argument(
        "--template",
        choices=["basic", "data-science", "web"],
        default="basic",
        help="项目模板类型 (默认: basic)"
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 处理命令
    if args.command == "init":
        project_dir = args.project_name
        print(f"初始化新项目: {project_dir}")
        create_project_structure(project_dir)
        print("\n项目初始化完成!")
        print(f"进入项目目录: cd {project_dir}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
