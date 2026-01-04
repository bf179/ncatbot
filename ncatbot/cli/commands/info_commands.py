"""帮助和信息命令"""

import os
import sys
from typing import Optional

from ncatbot.cli.commands.registry import registry
from ncatbot.cli.utils.colors import (
    aliases,
    category,
    command,
    description,
    error,
    header,
    info,
    title,
    usage,
    warning,
)
from ncatbot.utils import ncatbot_config as config


@registry.register(
    "help",
    "显示帮助信息",
    "help [命令名|分类名]",
    aliases=["h", "?"],
    category="info",
)
def show_command_help(command_name: Optional[str] = None) -> None:
    """显示命令帮助信息"""
    if command_name is None:
        show_help(config.bot_uin)
        return

    # 检查是否是分类
    if command_name in registry.get_categories():
        print(registry.get_help(command_name))
        return

    # 检查是否是别名
    cmd_name = command_name
    if command_name in registry.aliases:
        cmd_name = registry.aliases[command_name]
        print(f"'{command(command_name)}' 是 '{command(cmd_name)}' 的别名")

    # 显示特定命令的帮助
    if cmd_name not in registry.commands:
        print(error(f"不支持的命令: {command_name}"))
        return

    cmd = registry.commands[cmd_name]
    print(f"{header('命令:')} {command(cmd.name)}")
    print(f"{header('分类:')} {category(cmd.category)}")
    print(f"{header('用法:')} {usage(cmd.usage)}")
    print(f"{header('描述:')} {description(cmd.description)}")
    if cmd.help_text and cmd.help_text != cmd.description:
        print(f"{header('详细说明:')} {description(cmd.help_text)}")
    if cmd.aliases:
        print(f"{header('别名:')} {', '.join([aliases(a) for a in cmd.aliases])}")


@registry.register(
    "meta",
    "显示版本信息",
    "meta",
    aliases=["version", "v"],
    category="info",
)
def show_meta() -> None:
    """显示 NcatBot 版本信息"""
    try:
        import pkg_resources

        version = pkg_resources.get_distribution("ncatbot").version
        print(f"{header('NcatBot 版本:')} {info(version)}")
        print(f"{header('Python 版本:')} {info(sys.version.split()[0])}")
        print(f"{header('操作系统:')} {info(sys.platform)}")
        print(f"{header('工作目录:')} {info(os.getcwd())}")
        print(f"{header('机器人 QQ:')} {info(config.bot_uin or '未设置')}")
    except (ImportError, Exception) as e:
        print(error(f"无法获取版本信息: {e}"))


@registry.register(
    "categories",
    "显示命令分类",
    "categories [分类名]",
    aliases=["cat"],
    category="info",
)
def show_categories(filter_category: Optional[str] = None) -> None:
    """显示命令分类或特定分类下的命令"""
    categories_list = registry.get_categories()
    if not categories_list:
        print(warning("没有可用的命令分类"))
        return

    # 按分类过滤
    if filter_category:
        valid_filters = list(categories_list)
        if filter_category.lower() not in valid_filters:
            print(warning(f"未知的分类: {filter_category}"))
            print(
                info(f"可用的分类: {', '.join([category(c) for c in valid_filters])}")
            )
            return

        # 显示指定分类下的命令
        filter_cat = filter_category.lower()
        commands = registry.get_commands_by_category(filter_cat)
        if not commands:
            print(warning(f"分类 {category(filter_cat)} 中没有命令"))
            return

        print(header(f"分类 {category(filter_cat)} 中的命令:"))
        for i, (cmd_name, cmd) in enumerate(commands, 1):
            alias_text = ""
            if cmd.aliases:
                alias_list = [aliases(a) for a in cmd.aliases]
                alias_text = f" (别名: {', '.join(alias_list)})"
            print(
                f"{i}. {command(cmd.usage)} - {description(cmd.description)}{alias_text}"
            )
        return

    # 显示所有分类
    print(header("可用的命令分类:"))
    for i, cat_name in enumerate(categories_list, 1):
        commands = registry.get_commands_by_category(cat_name)
        print(f"{i}. {category(cat_name)} ({info(str(len(commands)))} 个命令)")


def show_help(qq: str) -> None:
    """显示简化的帮助信息"""
    print(title("NcatBot CLI"))
    print(f"{header('当前 QQ 号:')} {info(qq)}")
    print("")
    print(f"使用 {command('help <命令名>')} 查看特定命令的详细帮助")
    print(f"使用 {command('cat <分类名>')} 查看特定分类的命令")
    print("")
    print(registry.get_help())
