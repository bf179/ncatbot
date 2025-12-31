"""
测试用例定义

定义测试用例、测试结果等核心数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional


class TestStatus(Enum):
    """测试状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    PASSED = "passed"  # 通过
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过
    ERROR = "error"  # 执行错误


@dataclass
class TestCase:
    """
    测试用例定义

    Attributes:
        name: 测试名称
        description: 测试描述
        category: 测试分类（如 account, message, group）
        api_endpoint: 测试的 API 端点
        expected: 预期结果描述
        func: 测试函数
        tags: 标签列表
        requires_input: 是否需要人工输入测试数据
        cleanup: 清理函数（可选）
    """

    name: str
    description: str
    category: str
    api_endpoint: str
    expected: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    tags: List[str] = field(default_factory=list)
    requires_input: bool = False
    cleanup: Optional[Callable[..., Coroutine[Any, Any, None]]] = None

    def __repr__(self) -> str:
        return f"TestCase({self.name})"


@dataclass
class TestResult:
    """
    测试结果

    Attributes:
        test_case: 关联的测试用例
        status: 测试状态
        actual_result: 实际结果
        error: 错误信息（如果有）
        human_comment: 人工评语
        started_at: 开始时间
        finished_at: 结束时间
    """

    test_case: TestCase
    status: TestStatus = TestStatus.PENDING
    actual_result: Any = None
    error: Optional[str] = None
    human_comment: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        """执行时长（秒）"""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def mark_passed(self, comment: str = "") -> None:
        """标记为通过"""
        self.status = TestStatus.PASSED
        self.human_comment = comment
        self.finished_at = datetime.now()

    def mark_failed(self, comment: str = "") -> None:
        """标记为失败"""
        self.status = TestStatus.FAILED
        self.human_comment = comment
        self.finished_at = datetime.now()

    def mark_skipped(self, reason: str = "") -> None:
        """标记为跳过"""
        self.status = TestStatus.SKIPPED
        self.human_comment = reason
        self.finished_at = datetime.now()

    def mark_error(self, error: str) -> None:
        """标记为错误"""
        self.status = TestStatus.ERROR
        self.error = error
        self.finished_at = datetime.now()


def test_case(
    name: str,
    description: str,
    category: str,
    api_endpoint: str,
    expected: str,
    tags: List[str] = None,
    requires_input: bool = False,
):
    """
    测试用例装饰器

    用于将函数标记为测试用例。

    Example:
        @test_case(
            name="获取登录信息",
            description="获取当前登录的 QQ 账号信息",
            category="account",
            api_endpoint="/get_login_info",
            expected="返回包含 user_id 和 nickname 的信息",
        )
        async def test_get_login_info(api):
            return await api.get_login_info()
    """

    def decorator(func: Callable) -> TestCase:
        return TestCase(
            name=name,
            description=description,
            category=category,
            api_endpoint=api_endpoint,
            expected=expected,
            func=func,
            tags=tags or [],
            requires_input=requires_input,
        )

    return decorator
