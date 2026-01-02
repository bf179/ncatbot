"""
插件初始加载测试

测试插件加载时所有组件的正确注册。
"""

import time

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils import run_coroutine
from .conftest import (
    check_command_registered,
    check_alias_registered,
    check_config_registered,
    check_handler_registered,
)


PLUGIN_NAME = "HotReloadTestPlugin"


class TestInitialLoad:
    """插件初始加载测试"""

    def test_plugin_loads_successfully(self, reset_plugin_counters):
        """测试插件能成功加载"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            assert loader is not None

            # 通过正常流程加载插件
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            plugin = loader.get_plugin(PLUGIN_NAME)
            assert plugin is not None, f"插件 {PLUGIN_NAME} 应该已加载"
            assert plugin.name == PLUGIN_NAME

    def test_commands_registered_on_load(self, reset_plugin_counters):
        """测试加载时命令正确注册"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            assert check_command_registered("hot_reload_test"), \
                "命令 'hot_reload_test' 应该已注册"
            assert check_command_registered("hot_reload_config"), \
                "命令 'hot_reload_config' 应该已注册"

    def test_aliases_registered_on_load(self, reset_plugin_counters):
        """测试加载时别名正确注册"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            assert check_alias_registered("hrt"), \
                "别名 'hrt' 应该已注册"
            assert check_alias_registered("hrc"), \
                "别名 'hrc' 应该已注册"

    def test_config_registered_on_load(self, reset_plugin_counters):
        """测试加载时配置正确注册"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            assert check_config_registered(suite, PLUGIN_NAME), \
                "插件配置应该已注册"

            config_service = suite.services.plugin_config
            registered = config_service.get_registered_configs(PLUGIN_NAME)
            assert "reload_count" in registered
            assert "test_string" in registered

    def test_handler_registered_on_load(self, reset_plugin_counters):
        """测试加载时事件处理器正确注册"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            handler_count = check_handler_registered(suite, PLUGIN_NAME)
            assert handler_count > 0, "应该有至少一个事件处理器已注册"

    def test_command_works_after_load(self, reset_plugin_counters):
        """测试加载后命令能正常工作"""
        with E2ETestSuite(skip_builtin_plugins=True) as suite:
            loader = suite.client.plugin_loader
            run_coroutine(loader.load_plugins)
            time.sleep(0.1)

            suite.inject_group_message_sync("/hot_reload_test")
            time.sleep(0.1)

            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) >= 1
            message = str(calls[-1].get("message", ""))
            assert "热重载测试" in message
