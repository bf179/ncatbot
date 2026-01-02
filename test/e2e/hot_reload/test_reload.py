"""
插件重载测试

测试通过 SystemManager 卸载后重新加载插件的完整流程。
"""

import time

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils import run_coroutine
from ncatbot.core import NcatBotEvent, NcatBotEventFactory
from .conftest import (
    check_command_registered,
    check_alias_registered,
    check_handler_registered,
)


PLUGIN_NAME = "HotReloadTestPlugin"


class TestReload:
    """插件重载测试"""

    def test_reload_restores_commands(self, reset_plugin_counters):
        """测试重载后命令正确恢复"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader

            # 加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)
            assert check_command_registered("hot_reload_test")

            # 卸载插件
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)
            assert not check_command_registered("hot_reload_test")

            # 重新加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 验证命令已恢复
            assert check_command_registered("hot_reload_test"), \
                "命令 'hot_reload_test' 应该已恢复"
            assert check_alias_registered("hrt"), \
                "别名 'hrt' 应该已恢复"

    def test_reload_restores_handlers(self, reset_plugin_counters):
        """测试重载后事件处理器正确恢复"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader

            # 加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)
            assert check_handler_registered(suite, PLUGIN_NAME) > 0

            # 卸载插件
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)

            # 重新加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 验证处理器已恢复
            assert check_handler_registered(suite, PLUGIN_NAME) > 0, \
                "事件处理器应该已恢复"

    def test_reload_preserves_config_values(self, reset_plugin_counters):
        """测试重载后配置值被保留"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader
            config_service = suite.services.plugin_config

            # 加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)

            # 设置配置值（使用 set_atomic 确保持久化）
            config_service.set_atomic(PLUGIN_NAME, "test_string", "modified_value")
            config_service.set_atomic(PLUGIN_NAME, "reload_count", 10)

            # 卸载插件
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)

            # 验证配置值仍然存在
            stored_config = config_service.get_plugin_config(PLUGIN_NAME)
            assert stored_config.get("test_string") == "modified_value"
            assert stored_config.get("reload_count") == 10

            # 重新加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 验证插件可以访问保留的配置
            plugin = loader.get_plugin(PLUGIN_NAME)
            assert plugin is not None
            assert plugin.config.get("reload_count") == 10

    def test_reload_allows_config_re_registration(self, reset_plugin_counters):
        """测试重载后可以重新注册配置项"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader
            config_service = suite.services.plugin_config

            # 第一次加载
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)
            registered = config_service.get_registered_configs(PLUGIN_NAME)
            assert "reload_count" in registered

            # 卸载插件
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)

            # 验证配置项注册已清理
            registered = config_service.get_registered_configs(PLUGIN_NAME)
            assert len(registered) == 0

            # 第二次加载（应该可以重新注册配置项）
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 验证配置项重新注册成功
            registered = config_service.get_registered_configs(PLUGIN_NAME)
            assert "reload_count" in registered, "配置项应该可以重新注册"

    def test_command_works_after_reload(self, reset_plugin_counters):
        """测试重载后命令正常工作"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader

            # 加载、卸载、重新加载
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)

            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)

            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 验证命令工作
            suite.inject_group_message_sync("/hot_reload_test")
            time.sleep(0.1)
            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            assert "热重载测试" in str(calls[-1].get("message", ""))

    def test_event_handler_works_after_reload(self, reset_plugin_counters):
        """测试重载后事件处理器正常工作"""
        from test.e2e.hot_reload.fixtures.plugins.HotReloadTestPlugin import plugin

        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader

            # 加载插件
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)

            # 发布测试事件
            test_event = NcatBotEvent(
                "ncatbot.hot_reload_test_event",
                data={"test": "value1"}
            )
            run_coroutine(suite.event_bus.publish, test_event)
            time.sleep(0.1)
            assert plugin.HANDLER_CALL_COUNT > 0

            # 重置计数器
            plugin.reset_counters()

            # 卸载并重新加载
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)

            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)

            # 再次发布测试事件
            test_event = NcatBotEvent(
                "ncatbot.hot_reload_test_event",
                data={"test": "value2"}
            )
            run_coroutine(suite.event_bus.publish, test_event)
            time.sleep(0.1)

            # 验证处理器被调用
            assert plugin.HANDLER_CALL_COUNT > 0, \
                "重载后事件处理器应该工作"

    def test_full_hot_reload_cycle(self, reset_plugin_counters):
        """测试完整的热重载周期"""
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            loader = suite.client.plugin_loader

            # 加载
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.1)
            assert check_command_registered("hot_reload_test")

            # 使用命令
            suite.inject_group_message_sync("/hot_reload_test")
            time.sleep(0.1)
            suite.assert_reply_sent()
            suite.clear_call_history()

            # 卸载
            unload_event = NcatBotEventFactory.create_event(
                "plugin_unload_request",
                name=PLUGIN_NAME
            )
            run_coroutine(suite.event_bus.publish, unload_event)
            time.sleep(0.2)
            assert not check_command_registered("hot_reload_test")

            # 重新加载
            run_coroutine(loader.load_plugin, PLUGIN_NAME)
            time.sleep(0.2)
            assert check_command_registered("hot_reload_test")

            # 再次使用命令
            suite.inject_group_message_sync("/hot_reload_test")
            time.sleep(0.1)
            suite.assert_reply_sent()

