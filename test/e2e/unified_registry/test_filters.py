"""过滤器端到端测试

测试：
- 群聊过滤器
- 私聊过滤器
- 管理员过滤器
- 组合过滤器
"""

import pytest


class TestGroupFilter:
    """群聊过滤器测试"""

    def test_group_only_in_group(self, filter_suite):
        """测试群聊命令在群聊中可用"""
        filter_suite.inject_group_message_sync("/group_only")
        filter_suite.assert_reply_sent("这是群聊专用命令")

    def test_group_only_in_private(self, filter_suite):
        """测试群聊命令在私聊中不可用"""
        filter_suite.clear_call_history()
        filter_suite.inject_private_message_sync("/group_only")
        filter_suite.assert_no_reply()


class TestPrivateFilter:
    """私聊过滤器测试"""

    def test_private_only_in_private(self, filter_suite):
        """测试私聊命令在私聊中可用"""
        filter_suite.inject_private_message_sync("/private_only")
        filter_suite.assert_reply_sent("这是私聊专用命令")

    def test_private_only_in_group(self, filter_suite):
        """测试私聊命令在群聊中不可用"""
        filter_suite.clear_call_history()
        filter_suite.inject_group_message_sync("/private_only")
        filter_suite.assert_no_reply()


class TestAdminFilter:
    """管理员过滤器测试"""

    def test_ban_as_admin(self, filter_suite, mock_admin):
        """测试管理员可以使用封禁命令"""
        filter_suite.inject_private_message_sync("/ban 12345")
        filter_suite.assert_reply_sent("已封禁用户: 12345")

    def test_ban_as_non_admin(self, filter_suite, mock_non_admin):
        """测试非管理员不能使用封禁命令"""
        filter_suite.clear_call_history()
        filter_suite.inject_private_message_sync("/ban 12345")
        filter_suite.assert_no_reply()

    def test_kick_as_admin(self, filter_suite, mock_admin):
        """测试管理员可以使用踢出命令"""
        filter_suite.clear_call_history()
        filter_suite.inject_private_message_sync("/kick 12345")
        filter_suite.assert_reply_sent("已踢出用户: 12345")

    def test_kick_as_non_admin(self, filter_suite, mock_non_admin):
        """测试非管理员不能使用踢出命令"""
        filter_suite.clear_call_history()
        filter_suite.inject_private_message_sync("/kick 12345")
        filter_suite.assert_no_reply()


class TestCombinedFilters:
    """组合过滤器测试"""

    def test_mute_as_admin_in_group(self, filter_suite, mock_admin):
        """测试群聊中管理员可以禁言"""
        filter_suite.inject_group_message_sync("/mute 12345 300")
        filter_suite.assert_reply_sent("已禁言用户 12345")

    def test_mute_as_admin_in_private(self, filter_suite, mock_admin):
        """测试私聊中管理员不能禁言（需要群聊）"""
        filter_suite.clear_call_history()
        filter_suite.inject_private_message_sync("/mute 12345 300")
        filter_suite.assert_no_reply()

    def test_mute_as_non_admin_in_group(self, filter_suite, mock_non_admin):
        """测试群聊中非管理员不能禁言"""
        filter_suite.clear_call_history()
        filter_suite.inject_group_message_sync("/mute 12345 300")
        filter_suite.assert_no_reply()
