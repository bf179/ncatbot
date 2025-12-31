"""
API 测试基类

提供测试用例收集和管理功能。
"""

import sys
from pathlib import Path
from typing import List, Type

# 确保可以导入 framework
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import TestCase


class APITestSuite:
    """
    API 测试套件基类

    子类通过定义 test_* 属性（TestCase 实例）来添加测试用例。
    """

    # 测试套件名称
    suite_name: str = "API Tests"
    # 测试套件描述
    suite_description: str = ""

    @classmethod
    def collect_tests(cls) -> List[TestCase]:
        """
        收集所有测试用例

        Returns:
            测试用例列表
        """
        tests = []
        for name in dir(cls):
            if name.startswith("test_"):
                attr = getattr(cls, name)
                if isinstance(attr, TestCase):
                    tests.append(attr)
        return tests

    @classmethod
    def get_test_count(cls) -> int:
        """获取测试用例数量"""
        return len(cls.collect_tests())


def collect_all_tests(*suites: Type[APITestSuite]) -> List[TestCase]:
    """
    从多个测试套件收集所有测试用例

    Args:
        suites: 测试套件类列表

    Returns:
        所有测试用例
    """
    all_tests = []
    for suite in suites:
        all_tests.extend(suite.collect_tests())
    return all_tests
