"""插件管理命令"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional

from ncatbot.cli.commands.registry import registry
from ncatbot.cli.utils.colors import command, error, header, info, success, warning
from ncatbot.utils import ncatbot_config as config

# 模板目录路径
TEMPLATE_DIR = (
    Path(__file__).parent.parent.parent / "utils" / "assets" / "template_plugin"
)


@registry.register(
    "create",
    "创建插件模板",
    "create <插件名>",
    aliases=["new", "template"],
    category="plg",
)
def create_plugin_template(
    name: Optional[str] = None,
    author: Optional[str] = None,
    non_interactive: bool = False,
) -> None:
    """创建新插件模板"""
    if name is None:
        name = input(info("请输入插件名称: ")).strip()

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        print(
            error(
                f"插件名 '{command(name)}' 不合法! 插件名必须以字母开头，只能包含字母、数字和下划线。"
            )
        )
        return

    # 确保插件目录存在
    try:
        os.makedirs(config.plugin.plugins_dir, exist_ok=True)
    except Exception as e:
        print(error(f"无法创建插件目录: {e}"))
        return

    plugin_dir = Path(config.plugin.plugins_dir) / name
    if plugin_dir.exists():
        print(warning(f"插件目录 '{command(name)}' 已存在!"))
        if not non_interactive and input(warning("是否覆盖? (y/n): ")).lower() not in [
            "y",
            "yes",
        ]:
            return
        shutil.rmtree(plugin_dir)

    try:
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # 获取作者名称
        if author is None:
            if non_interactive:
                author = "Your Name"
            else:
                author_input = input(info("请输入作者名称 (默认: Your Name): ")).strip()
                author = author_input if author_input else "Your Name"

        # 检查模板目录
        if not TEMPLATE_DIR.exists():
            print(error(f"模板目录不存在: {TEMPLATE_DIR}"))
            return

        # 复制模板文件（使用 UTF-8 编码保证跨平台兼容性）
        for file in TEMPLATE_DIR.iterdir():
            if file.is_file():
                # 使用 UTF-8 编码读取源文件
                try:
                    content = file.read_text(encoding="utf-8")
                    (plugin_dir / file.name).write_text(content, encoding="utf-8")
                except Exception:
                    # 如果 UTF-8 失败，使用二进制复制作为备选
                    shutil.copy2(file, plugin_dir / file.name)

        # 替换模板内容
        replacements = {
            "plugin.py": {
                "class Plugin(NcatBotPlugin)": f"class {name}(NcatBotPlugin)",
            },
            "__init__.py": {
                "from .plugin import Plugin as Plugin": f"from .plugin import {name} as {name}",
            },
            "README.md": {
                "Plugin Name": name,
                "Your Name": author,
            },
            "manifest.toml": {
                'name = "Plugin Name"': f'name = "{name}"',
                'author = "Your Name"': f'author = "{author}"',
                'entry_class = "Plugin"': f'entry_class = "{name}"',
            },
        }

        for file, file_replacements in replacements.items():
            file_path = plugin_dir / file
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                for old_str, new_str in file_replacements.items():
                    content = content.replace(old_str, new_str)
                file_path.write_text(content, encoding="utf-8")

        print(success(f"插件模板 '{command(name)}' 创建成功!"))
        print(info(f"插件目录: {plugin_dir}"))
        print(info("请修改插件信息并添加功能代码。"))

    except Exception as e:
        print(error(f"创建插件模板时出错: {e}"))
        if plugin_dir.exists():
            try:
                shutil.rmtree(plugin_dir)
            except Exception:
                pass


@registry.register(
    "remove",
    "卸载插件",
    "remove <插件名>",
    aliases=["rm", "uninstall"],
    category="plg",
)
def remove_plugin(plugin_name: Optional[str] = None) -> None:
    """删除插件目录"""
    if plugin_name is None:
        plugin_name = input(info("请输入要删除的插件名称: ")).strip()

    plugin_dir = Path(config.plugin.plugins_dir) / plugin_name
    if not plugin_dir.exists():
        print(error(f"插件 {command(plugin_name)} 不存在!"))
        return

    confirm = input(warning(f"确定要删除插件 {command(plugin_name)}? (y/n): "))
    if confirm.lower() not in ["y", "yes"]:
        print(info("已取消删除"))
        return

    shutil.rmtree(plugin_dir)
    print(success(f"插件 {command(plugin_name)} 已删除!"))


@registry.register(
    "list",
    "列出已安装插件",
    "list",
    aliases=["ls"],
    category="plg",
)
def list_plugins() -> None:
    """列出插件目录中的所有插件"""
    plugins_dir = Path(config.plugin.plugins_dir)

    if not plugins_dir.exists():
        print(warning("插件目录不存在"))
        return

    plugin_dirs = [d for d in plugins_dir.iterdir() if d.is_dir()]
    if not plugin_dirs:
        print(warning("没有安装任何插件"))
        return

    print(header("已安装插件:"))
    print(f"  插件目录: {info(str(plugins_dir))}\n")

    for i, plugin_dir in enumerate(sorted(plugin_dirs), 1):
        manifest_path = plugin_dir / "manifest.toml"
        if manifest_path.exists():
            try:
                try:
                    import tomllib
                except ModuleNotFoundError:
                    import tomli as tomllib

                manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
                name = manifest.get("name", plugin_dir.name)
                version = manifest.get("version", "未知")
                author = manifest.get("author", "未知")
                description = manifest.get("description", "")

                print(f"  {i}. {command(name)} v{version}")
                print(f"     作者: {author}")
                if description:
                    print(f"     描述: {description}")
            except Exception:
                print(f"  {i}. {command(plugin_dir.name)} (manifest 解析失败)")
        else:
            print(f"  {i}. {command(plugin_dir.name)} (无 manifest)")
