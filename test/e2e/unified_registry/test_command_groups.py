"""命令分组端到端测试

测试：
- 使用 group() 创建的命令组
- 组内子命令（层级命令）
- 独立命令
"""

import pytest


class TestIndependentCommands:
    """独立命令测试（对照组）"""

    def test_help_command(self, groups_suite):
        """测试帮助命令"""
        groups_suite.inject_private_message_sync("/help")
        groups_suite.assert_reply_sent("可用命令组: user, config")

    def test_help_with_param(self, groups_suite):
        """测试带参数的帮助命令"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/help deploy")
        groups_suite.assert_reply_sent("命令 deploy 的帮助信息")


class TestUserGroupCommands:
    """用户组命令测试（层级命令）"""

    def test_user_info_command(self, groups_suite):
        """测试用户信息命令"""
        groups_suite.inject_private_message_sync("/user info 12345")
        groups_suite.assert_reply_sent("用户 12345 的信息")

    def test_user_list_command(self, groups_suite):
        """测试用户列表命令"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/user list")
        groups_suite.assert_reply_sent("用户列表 (第 1 页)")

    def test_user_list_with_page(self, groups_suite):
        """测试用户列表带页码"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/user list 3")
        groups_suite.assert_reply_sent("用户列表 (第 3 页)")

    def test_user_search_command(self, groups_suite):
        """测试用户搜索命令"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/user search admin")
        groups_suite.assert_reply_sent("搜索用户: admin")


class TestConfigGroupCommands:
    """配置组命令测试（层级命令）"""

    def test_config_get_command(self, groups_suite):
        """测试获取配置命令"""
        groups_suite.inject_private_message_sync("/config get debug_mode")
        groups_suite.assert_reply_sent("配置项 debug_mode 的值: (mock)")

    def test_config_set_command(self, groups_suite):
        """测试设置配置命令"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/config set debug_mode true")
        groups_suite.assert_reply_sent("已设置 debug_mode = true")

    def test_config_list_command(self, groups_suite):
        """测试列出配置命令"""
        groups_suite.clear_call_history()
        groups_suite.inject_private_message_sync("/config list")
        groups_suite.assert_reply_sent("所有配置项列表")
