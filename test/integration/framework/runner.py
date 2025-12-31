"""
交互式测试运行器

逐个执行测试用例，展示结果，等待人工确认。
"""

import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from .case import TestCase, TestResult, TestStatus


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
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"


class InteractiveTestRunner:
    """
    交互式测试运行器

    逐个执行测试，人工确认结果。

    Features:
        - 逐个执行测试用例
        - 展示详细的测试信息和结果
        - 支持人工确认通过/失败/跳过
        - 支持重试
        - 生成测试报告
    """

    def __init__(self, api: Any, config: Dict[str, Any] = None):
        """
        Args:
            api: BotAPI 实例
            config: 测试配置（如测试群号、测试用户等）
        """
        self.api = api
        self.config = config or {}
        self.results: List[TestResult] = []
        self._current_index = 0

    def _print_header(self, text: str) -> None:
        """打印标题"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

    def _print_section(self, title: str, content: str) -> None:
        """打印章节"""
        print(f"{Colors.CYAN}{Colors.BOLD}[{title}]{Colors.ENDC}")
        print(f"  {content}")

    def _print_result(self, result: Any) -> None:
        """格式化打印结果"""
        print(f"{Colors.CYAN}{Colors.BOLD}[实际结果]{Colors.ENDC}")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"  {Colors.DIM}{key}:{Colors.ENDC} {value}")
        elif hasattr(result, "__dict__"):
            for key, value in vars(result).items():
                if not key.startswith("_"):
                    print(f"  {Colors.DIM}{key}:{Colors.ENDC} {value}")
        else:
            print(f"  {result}")

    def _print_status(self, status: TestStatus) -> None:
        """打印状态"""
        color_map = {
            TestStatus.PASSED: Colors.GREEN,
            TestStatus.FAILED: Colors.RED,
            TestStatus.SKIPPED: Colors.YELLOW,
            TestStatus.ERROR: Colors.RED,
            TestStatus.PENDING: Colors.DIM,
            TestStatus.RUNNING: Colors.BLUE,
        }
        color = color_map.get(status, Colors.ENDC)
        print(f"{color}{Colors.BOLD}[{status.value.upper()}]{Colors.ENDC}")

    def _get_user_action(self) -> str:
        """获取用户操作"""
        print(f"\n{Colors.YELLOW}请选择操作:{Colors.ENDC}")
        print(f"  {Colors.GREEN}[p]{Colors.ENDC} 通过 (Pass)")
        print(f"  {Colors.RED}[f]{Colors.ENDC} 失败 (Fail)")
        print(f"  {Colors.YELLOW}[s]{Colors.ENDC} 跳过 (Skip)")
        print(f"  {Colors.BLUE}[r]{Colors.ENDC} 重试 (Retry)")
        print(f"  {Colors.CYAN}[c]{Colors.ENDC} 添加评论 (Comment)")
        print(f"  {Colors.DIM}[q]{Colors.ENDC} 退出 (Quit)")

        while True:
            action = input(f"\n{Colors.BOLD}> {Colors.ENDC}").strip().lower()
            if action in ["p", "f", "s", "r", "c", "q", "pass", "fail", "skip", "retry", "comment", "quit"]:
                return action[0]
            print(f"{Colors.RED}无效输入，请重新选择{Colors.ENDC}")

    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """执行单个测试"""
        result = TestResult(test_case=test_case)
        result.started_at = datetime.now()
        result.status = TestStatus.RUNNING

        # 打印测试信息
        self._print_header(f"测试: {test_case.name}")
        self._print_section("描述", test_case.description)
        self._print_section("API", test_case.api_endpoint)
        self._print_section("分类", test_case.category)
        self._print_section("预期结果", test_case.expected)

        if test_case.tags:
            self._print_section("标签", ", ".join(test_case.tags))

        print(f"\n{Colors.BLUE}正在执行测试...{Colors.ENDC}\n")

        try:
            # 执行测试
            actual = await test_case.func(self.api, self.config)
            result.actual_result = actual
            self._print_result(actual)
        except Exception as e:
            result.error = traceback.format_exc()
            print(f"\n{Colors.RED}{Colors.BOLD}[执行错误]{Colors.ENDC}")
            print(f"  {Colors.RED}{e}{Colors.ENDC}")
            print(f"\n{Colors.DIM}{result.error}{Colors.ENDC}")

        return result

    async def _handle_test_result(self, result: TestResult) -> bool:
        """
        处理测试结果，返回是否继续

        Returns:
            True: 继续下一个测试
            False: 退出测试
        """
        comment = ""

        while True:
            action = self._get_user_action()

            if action == "p":
                result.mark_passed(comment)
                self._print_status(TestStatus.PASSED)
                return True

            elif action == "f":
                result.mark_failed(comment)
                self._print_status(TestStatus.FAILED)
                return True

            elif action == "s":
                result.mark_skipped(comment or "用户跳过")
                self._print_status(TestStatus.SKIPPED)
                return True

            elif action == "r":
                # 重试
                return None  # 特殊标记，表示重试

            elif action == "c":
                comment = input(f"{Colors.CYAN}请输入评论: {Colors.ENDC}")
                print(f"{Colors.GREEN}评论已保存{Colors.ENDC}")
                continue

            elif action == "q":
                result.mark_skipped("用户退出")
                return False

    async def run_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        运行所有测试

        Args:
            test_cases: 测试用例列表

        Returns:
            测试结果列表
        """
        self.results = []
        total = len(test_cases)

        self._print_header("交互式 API 集成测试")
        print(f"共 {Colors.BOLD}{total}{Colors.ENDC} 个测试用例")
        print(f"\n{Colors.DIM}按任意键开始测试...{Colors.ENDC}")
        input()

        for i, test_case in enumerate(test_cases):
            self._current_index = i
            print(f"\n{Colors.DIM}[{i + 1}/{total}]{Colors.ENDC}")

            while True:
                result = await self._run_single_test(test_case)
                continue_flag = await self._handle_test_result(result)

                if continue_flag is None:
                    # 重试
                    print(f"\n{Colors.BLUE}重试测试...{Colors.ENDC}")
                    continue
                elif continue_flag:
                    self.results.append(result)
                    break
                else:
                    # 退出
                    self.results.append(result)
                    self._print_summary()
                    return self.results

        self._print_summary()
        return self.results

    async def run_single(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        while True:
            result = await self._run_single_test(test_case)
            continue_flag = await self._handle_test_result(result)

            if continue_flag is None:
                continue
            else:
                self.results.append(result)
                return result

    def _print_summary(self) -> None:
        """打印测试摘要"""
        self._print_header("测试摘要")

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        error = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        total = len(self.results)

        print(f"  {Colors.GREEN}通过: {passed}{Colors.ENDC}")
        print(f"  {Colors.RED}失败: {failed}{Colors.ENDC}")
        print(f"  {Colors.YELLOW}跳过: {skipped}{Colors.ENDC}")
        print(f"  {Colors.RED}错误: {error}{Colors.ENDC}")
        print(f"  {Colors.BOLD}总计: {total}{Colors.ENDC}")

        if failed > 0 or error > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}失败的测试:{Colors.ENDC}")
            for r in self.results:
                if r.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    print(f"  - {r.test_case.name}: {r.human_comment or r.error or '无说明'}")

    def get_results(self) -> List[TestResult]:
        """获取所有测试结果"""
        return self.results.copy()
