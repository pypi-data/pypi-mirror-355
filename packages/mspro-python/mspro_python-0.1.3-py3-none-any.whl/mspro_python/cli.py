# mspro_python/cli.py

import os
import shutil
from pathlib import Path
import click

TEMPLATE_DIR = Path(__file__).parent / "template" / "mspro_project"


@click.command()
@click.argument("project_name")
def main(project_name):
    target = Path.cwd() / project_name
    if target.exists():
        print(f"目录 {target} 已存在，取消创建。")
        return

    shutil.copytree(TEMPLATE_DIR, target)
    print(f"✅ 已创建新项目: {target}")


if __name__ == "__main__":
    main()
