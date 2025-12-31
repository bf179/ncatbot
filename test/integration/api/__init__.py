"""
API 集成测试模块
"""

from .base import APITestSuite
from .test_account import AccountAPITests
from .test_message import MessageAPITests
from .test_group import GroupAPITests

__all__ = [
    "APITestSuite",
    "AccountAPITests",
    "MessageAPITests",
    "GroupAPITests",
]
