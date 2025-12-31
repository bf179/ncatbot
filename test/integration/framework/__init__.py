"""
交互式集成测试框架

提供人工确认的 API 测试能力。
"""

from .runner import InteractiveTestRunner
from .reporter import TestReporter
from .case import TestCase, TestResult, TestStatus, test_case

__all__ = [
    "InteractiveTestRunner",
    "TestReporter",
    "TestCase",
    "TestResult",
    "TestStatus",
    "test_case",
]
