"""配置管理命令"""

from typing import Optional

from ncatbot.cli.commands.registry import registry
from ncatbot.cli.utils.colors import command, error, info, success
from ncatbot.utils import ncatbot_config as config


@registry.register(
    "setqq",
    "设置机器人 QQ 号",
    "setqq [QQ号]",
    aliases=["qq"],
    category="sys",
)
def set_qq(qq: Optional[str] = None) -> str:
    """设置机器人 QQ 号"""
    if qq is None:
        qq = input(info("请输入 QQ 号: "))

    if not qq.isdigit():
        print(error("QQ 号必须为数字!"))
        return set_qq()

    qq_confirm = input(info(f"请再输入一遍 QQ 号 {command(qq)} 并确认: "))
    if qq != qq_confirm:
        print(error("两次输入的 QQ 号不一致!"))
        return set_qq()

    config.bot_uin = qq
    config.save()
    print(success(f"QQ 号已设置为 {qq}"))
    return qq


@registry.register(
    "setroot",
    "设置管理员 QQ 号",
    "setroot [QQ号]",
    aliases=["root"],
    category="sys",
)
def set_root(qq: Optional[str] = None) -> str:
    """设置管理员 QQ 号"""
    if qq is None:
        qq = input(info("请输入管理员 QQ 号: "))

    if not qq.isdigit():
        print(error("QQ 号必须为数字!"))
        return set_root()

    config.root = qq
    config.save()
    print(success(f"管理员 QQ 号已设置为 {qq}"))
    return qq


@registry.register(
    "config",
    "查看当前配置",
    "config",
    aliases=["cfg"],
    category="sys",
)
def show_config() -> None:
    """显示当前配置"""
    from ncatbot.cli.utils.colors import header

    print(header("当前配置:"))
    print(f"  机器人 QQ: {info(config.bot_uin)}")
    print(f"  管理员 QQ: {info(config.root)}")
    print(f"  WebSocket URI: {info(config.napcat.ws_uri)}")
    print(f"  WebUI URI: {info(config.napcat.webui_uri)}")
    print(f"  插件目录: {info(config.plugin.plugins_dir)}")
    print(f"  调试模式: {info(str(config.debug))}")
