"""
交互式 API 集成测试入口

运行方式:
    uv run python test/integration/run_api_tests.py

可选参数:
    --category <category>   只运行指定分类的测试 (account, message, group)
    --tag <tag>             只运行带有指定标签的测试
    --report <path>         保存测试报告到指定路径
    --config <path>         从 JSON 文件加载测试配置

示例:
    # 运行所有测试
    uv run python test/integration/run_api_tests.py

    # 只运行账号相关测试
    uv run python test/integration/run_api_tests.py --category account

    # 运行带有 basic 标签的测试
    uv run python test/integration/run_api_tests.py --tag basic

    # 生成报告
    uv run python test/integration/run_api_tests.py --report ./reports/api_test.md
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加 integration 目录到路径
integration_root = Path(__file__).parent
sys.path.insert(0, str(integration_root))

from ncatbot.core.api import BotAPI
from ncatbot.core.adapter import Adapter

from framework import InteractiveTestRunner, TestReporter, TestCase
from api import AccountAPITests, MessageAPITests, GroupAPITests
from api.base import collect_all_tests


class Colors:
    """终端颜色"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ███╗   ██╗ ██████╗ █████╗ ████████╗██████╗  ██████╗ ████████╗║
║     ████╗  ██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗╚══██╔══╝║
║     ██╔██╗ ██║██║     ███████║   ██║   ██████╔╝██║   ██║   ██║   ║
║     ██║╚██╗██║██║     ██╔══██║   ██║   ██╔══██╗██║   ██║   ██║   ║
║     ██║ ╚████║╚██████╗██║  ██║   ██║   ██████╔╝╚██████╔╝   ██║   ║
║     ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝    ╚═╝   ║
║                                                               ║
║              交互式 API 集成测试工具 v1.0                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.CYAN}{banner}{Colors.ENDC}")


def filter_tests(
    tests: List[TestCase],
    category: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[TestCase]:
    """过滤测试用例"""
    filtered = tests

    if category:
        filtered = [t for t in filtered if t.category == category]

    if tag:
        filtered = [t for t in filtered if tag in t.tags]

    return filtered


def print_test_list(tests: List[TestCase]):
    """打印测试列表"""
    print(f"\n{Colors.BOLD}即将运行的测试用例:{Colors.ENDC}\n")

    # 按分类分组
    categories = {}
    for test in tests:
        if test.category not in categories:
            categories[test.category] = []
        categories[test.category].append(test)

    for category, category_tests in categories.items():
        print(f"{Colors.CYAN}[{category.upper()}]{Colors.ENDC}")
        for i, test in enumerate(category_tests, 1):
            tags = f" {Colors.YELLOW}[{', '.join(test.tags)}]{Colors.ENDC}" if test.tags else ""
            input_mark = f" {Colors.RED}*{Colors.ENDC}" if test.requires_input else ""
            print(f"  {i}. {test.name}{tags}{input_mark}")
        print()

    print(f"{Colors.RED}* 表示需要人工输入测试数据{Colors.ENDC}\n")


async def setup_connection() -> BotAPI:
    """建立连接并返回 BotAPI"""
    print(f"{Colors.BLUE}正在连接 NapCat 服务...{Colors.ENDC}")

    adapter = Adapter()

    # 尝试连接
    from ncatbot.core.adapter.nc import napcat_service_ok

    if not napcat_service_ok(timeout=5):
        print(f"{Colors.RED}错误: 无法连接到 NapCat 服务{Colors.ENDC}")
        print(f"{Colors.YELLOW}请确保 NapCat 服务正在运行{Colors.ENDC}")
        sys.exit(1)

    # 创建 API
    api = BotAPI(adapter.send)
    print(f"{Colors.GREEN}连接成功!{Colors.ENDC}")

    # 获取登录信息
    try:
        login_info = await api.get_login_info()
        print(f"{Colors.GREEN}当前登录: {login_info.nickname} ({login_info.user_id}){Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.YELLOW}警告: 无法获取登录信息 - {e}{Colors.ENDC}")

    return api


def load_config(config_path: Optional[str]) -> dict:
    """加载测试配置"""
    config = {
        "target_group": None,
        "target_user": None,
        "last_message_id": None,
    }

    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
            print(f"{Colors.GREEN}已加载配置: {config_path}{Colors.ENDC}")
        except FileNotFoundError:
            print(f"{Colors.YELLOW}配置文件不存在: {config_path}{Colors.ENDC}")
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}配置文件格式错误: {e}{Colors.ENDC}")

    return config


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NcatBot API 集成测试工具")
    parser.add_argument("--category", "-c", help="只运行指定分类的测试")
    parser.add_argument("--tag", "-t", help="只运行带有指定标签的测试")
    parser.add_argument("--report", "-r", help="保存测试报告到指定路径")
    parser.add_argument("--config", help="从 JSON 文件加载测试配置")
    parser.add_argument("--list", "-l", action="store_true", help="只列出测试用例，不执行")

    args = parser.parse_args()

    print_banner()

    # 收集所有测试
    all_tests = collect_all_tests(
        AccountAPITests,
        MessageAPITests,
        GroupAPITests,
    )

    # 过滤测试
    tests = filter_tests(all_tests, category=args.category, tag=args.tag)

    if not tests:
        print(f"{Colors.RED}没有匹配的测试用例{Colors.ENDC}")
        sys.exit(1)

    print(f"找到 {Colors.BOLD}{len(tests)}{Colors.ENDC} 个测试用例")

    # 打印测试列表
    print_test_list(tests)

    if args.list:
        sys.exit(0)

    # 确认开始
    confirm = input(f"{Colors.YELLOW}是否开始测试? (y/n): {Colors.ENDC}").lower()
    if confirm != "y":
        print("已取消")
        sys.exit(0)

    # 加载配置
    config = load_config(args.config)

    # 建立连接
    api = await setup_connection()

    # 创建运行器
    runner = InteractiveTestRunner(api, config)

    # 运行测试
    results = await runner.run_tests(tests)

    # 生成报告
    if args.report:
        reporter = TestReporter(results)
        report_path = Path(args.report)

        # 根据扩展名决定格式
        if report_path.suffix == ".json":
            reporter.save(str(report_path), format="json")
        else:
            reporter.save(str(report_path), format="markdown")

    print(f"\n{Colors.GREEN}测试完成!{Colors.ENDC}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.ENDC}")
        sys.exit(1)
