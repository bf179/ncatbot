"""系统管理命令"""

from ncatbot.cli.commands.registry import registry
from ncatbot.cli.utils import CLIExit
from ncatbot.cli.utils.colors import error, header, info, success
from ncatbot.utils.logger import get_log

LOG = get_log("CLI")


@registry.register(
    "start",
    "启动 NcatBot",
    "start",
    aliases=["s", "run"],
    category="sys",
)
def start() -> None:
    """启动 NcatBot 客户端"""
    from ncatbot.core import BotClient

    print(header("正在启动 NcatBot..."))
    print(info("按下 Ctrl + C 可以正常退出程序"))

    try:
        client = BotClient()
        client.run()
    except Exception as e:
        LOG.error(f"启动失败: {e}")
        print(error(f"启动失败: {e}"))


@registry.register(
    "update",
    "更新 NcatBot",
    "update",
    aliases=["u", "upgrade"],
    category="sys",
)
def update() -> None:
    """更新 NcatBot 到最新版本"""
    import subprocess
    import sys

    from ncatbot.cli.utils import PYPI_SOURCE

    print(header("正在更新 NcatBot..."))

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "ncatbot",
                "-i",
                PYPI_SOURCE,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(success("NcatBot 更新成功!"))
            print(info("请重新启动 CLI 以使用新版本"))
        else:
            print(error(f"更新失败: {result.stderr}"))
    except Exception as e:
        print(error(f"更新时出错: {e}"))


@registry.register(
    "exit",
    "退出 CLI",
    "exit",
    aliases=["quit", "q"],
    category="sys",
)
def exit_cli() -> None:
    """退出 CLI 工具"""
    print("\n" + info("再见!"))
    raise CLIExit()
