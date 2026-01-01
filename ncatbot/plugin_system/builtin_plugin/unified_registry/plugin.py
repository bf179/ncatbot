"""统一注册插件"""

import asyncio
import traceback
from typing import Dict, Callable, TYPE_CHECKING, List, Tuple, Optional
from .command_system.utils import (
    CommandSpec,
)

from ncatbot.utils import get_log
from ...builtin_mixin import NcatBotPlugin
from .trigger.binder import BindResult
from .trigger.preprocessor import MessagePreprocessor, PreprocessResult
from .command_system.lexer.tokenizer import StringTokenizer, Token
from .trigger.resolver import CommandResolver
from .trigger.binder import ArgumentBinder
from .filter_system import filter_registry
from .filter_system.validator import FilterValidator
from .command_system.registry.registry import command_registry
from .legacy_registry import legacy_registry
from ncatbot.core import NcatBotEvent

# 兼容别名

if TYPE_CHECKING:
    from ncatbot.core import MessageEvent, BaseEvent

LOG = get_log("UnifiedRegistry")


class UnifiedRegistryPlugin(NcatBotPlugin):
    """统一注册插件

    提供过滤器和命令的统一管理功能。
    保持 plugin.py 简洁，具体逻辑分布在各个子模块中。
    """

    name = "UnifiedRegistryPlugin"
    author = "huan-yp"
    desc = "统一的过滤器和命令注册插件"
    version = "2.0.0"

    async def on_load(self) -> None:
        """插件加载时的初始化"""
        # 订阅事件
        self.event_bus.subscribe(
            "re:ncatbot.message_event|ncatbot.message_sent_event",
            self.handle_message_event,
            timeout=900,
        )
        self.event_bus.subscribe(
            "re:ncatbot.notice_event|ncatbot.request_event",
            self.handle_legacy_event,
            timeout=900,
        )
        self.event_bus.subscribe(
            "ncatbot.plugin_unload",
            self.handle_plugin_unload_event,
        )
        self.event_bus.subscribe(
            "ncatbot.plugin_load",
            self.handle_plugin_load_event,
        )

        # 设置过滤器验证器
        self._filter_validator = FilterValidator()

        # 初始化插件映射
        self.func_plugin_map: Dict[Callable, NcatBotPlugin] = {}

        # 触发引擎延迟到首次收到消息时再初始化
        self.filter_registry = filter_registry
        self.command_registry = command_registry
        self._trigger_engine = None
        self._binder = ArgumentBinder()
        self._initialized = False

    def _normalize_case(self, s: str) -> str:
        # TODO: 实现大小写敏感（可能永远不会做）
        return s

    async def handle_plugin_unload_event(self, event: "NcatBotEvent") -> None:
        """处理插件卸载事件，清理相关缓存"""
        LOG.debug(f"处理插件卸载事件: {event.data['name']}")
        self._initialized = False
        self.command_registry.root_group.revoke_plugin(event.data["name"])
        self.filter_registry.revoke_plugin(event.data["name"])
        self.initialize_if_needed()

    async def handle_plugin_load_event(self, event: "NcatBotEvent") -> None:
        """处理插件加载事件，清理相关缓存"""
        self._initialized = False
        self.initialize_if_needed()

    async def _execute_function(self, func: Callable, *args, **kwargs):
        """执行函数
        :args[0] 是事件对象
        """
        print(f"DEBUG: _execute_function called with {func.__name__}, args: {len(args)}, kwargs: {list(kwargs.keys())}")

        plugin = self._find_plugin_for_function(func)
        print(f"DEBUG: plugin found: {plugin}")
        try:
            # 使用新的过滤器验证器
            if hasattr(func, "__filters__"):
                if not self._filter_validator.validate_filters(func, args[0]):
                    return False
            args = (plugin,) + args if plugin else args
            if asyncio.iscoroutinefunction(func):
                # 异步处理器: 直接 await,不创建新的事件循环
                return await func(*args, **kwargs)
            else:
                # 同步处理器: 在线程池中执行,避免阻塞事件循环
                return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            LOG.error(f"执行函数 {func.__name__} 时发生错误: {e}")
            LOG.info(f"{traceback.format_exc()}")
            return False

    async def _run_pure_filters(self, event: "MessageEvent") -> None:
        """遍历执行纯过滤器函数（不含命令函数）。"""
        for func in filter_registry._function_filters.values():
            # 额外防御：若误标记，仍跳过命令函数
            if getattr(func, "__is_command__", False):
                continue
            await self._execute_function(func, event)

    async def _run_command(self, event: "MessageEvent") -> None:
        print(f"DEBUG: _run_command called")
        # 前置检查与提取首段文本（用于前缀与命令词匹配）
        pre: Optional[PreprocessResult] = self._preprocessor.precheck(event)
        print(f"DEBUG: precheck result: {pre}")
        if pre is None:
            # 不符合前置条件（例如不要求前缀但为空/非文本）
            print("DEBUG: precheck returned None, returning False")
            return False

        # 解析首段文本为 token（用于命令匹配）
        text = pre.command_text
        print(f"DEBUG: Processing text: '{text}'")
        first_word = text.split(" ")[0]
        print(f"DEBUG: first_word: '{first_word}'")

        commands = self._resolver.get_commands()
        print(f"DEBUG: Available commands: {[cmd.path_words for cmd in commands]}")
        hit = [
            command
            for command in commands
            if first_word.endswith(command.path_words[0])
        ]
        print(f"DEBUG: Hit commands: {[cmd.path_words for cmd in hit]}")
        if not hit:
            print("DEBUG: No commands matched, returning False")
            return False

        print(f"DEBUG: About to tokenize text: '{text}'")
        tokenizer = StringTokenizer(text)
        tokens: List[Token] = tokenizer.tokenize()
        print(f"DEBUG: Tokens: {[str(t) for t in tokens]}")

        # 从首段 token 流解析命令（严格无前缀冲突则应唯一）
        print("DEBUG: About to resolve from tokens")
        print("DEBUG: Calling resolve_from_tokens...")
        prefix, match = self._resolver.resolve_from_tokens(tokens)
        print(f"DEBUG: resolve_from_tokens returned: prefix='{prefix}', match={match is not None}")

        print(f"DEBUG: Checking match conditions: match is None: {match is None}")
        if match is None:
            print("DEBUG: match is None, returning False")
            return False
        print(f"DEBUG: prefix: '{prefix}', match.command.prefixes: {match.command.prefixes}")
        print(f"DEBUG: prefix in prefixes: {prefix in match.command.prefixes}")
        if prefix not in match.command.prefixes:
            print(f"DEBUG: prefix '{prefix}' not in prefixes {match.command.prefixes}, returning False")
            return False

        LOG.info(f"命中命令: {match.command.func.__name__}")
        print(f"DEBUG: Command matched successfully: {match.command.func.__name__}")

        func = match.command.func
        ignore_words = match.path_words  # 用于参数绑定的 ignore 计数

        print("DEBUG: About to bind parameters")
        try:
            bind_result: BindResult = self._binder.bind(
                match.command, event, ignore_words, [prefix]
            )
            print(f"DEBUG: Parameter binding successful: args={bind_result.args}, kwargs={bind_result.named_args}")
        except Exception as e:
            print(f"DEBUG: Parameter binding failed: {e}")
            await self.event_bus.publish(
                NcatBotEvent(
                    type="ncatbot.param_bind_failed",
                    data={"event": event, "msg": str(e), "cmd": match.command.name},
                )
            )
            return False

        print(f"DEBUG: About to execute {func.__name__}")
        try:
            await self._execute_function(
                func, event, *bind_result.args, **bind_result.named_args
            )
            print(f"DEBUG: Function execution completed")
        except Exception as e:
            print(f"DEBUG: Exception during command execution: {e}")
            import traceback
            traceback.print_exc()

    async def handle_message_event(self, event: "NcatBotEvent") -> bool:
        """处理消息事件（命令和过滤器）"""
        print(f"DEBUG: handle_message_event called for {event.type}")
        # 惰性初始化
        self.initialize_if_needed()
        print("DEBUG: About to call _run_command")
        await self._run_command(event.data)
        await self._run_pure_filters(event.data)

    def initialize_if_needed(self) -> None:
        """首次触发时构建命令分发表并做严格冲突检测。"""
        if self._initialized:
            return

        self._initialized = True

        self.prefixes = list(
            dict.fromkeys(
                prefix
                for registry in command_registry.command_registries
                for prefix in registry.prefixes
            )
        )
        if "" in self.prefixes:
            self.prefixes.remove("")
        LOG.info(f"命令前缀集合: {self.prefixes}")

        self._preprocessor = MessagePreprocessor(
            prefixes=self.prefixes,
            require_prefix=False,
            case_sensitive=False,
        )

        self._resolver = CommandResolver(
            allow_hierarchical=False,
            prefixes=self.prefixes,
            case_sensitive=False,
        )

        # 1) 检查消息级前缀集合冲突
        norm_prefixes = [self._normalize_case(p) for p in self._preprocessor.prefixes]
        for i, p1 in enumerate(norm_prefixes):
            for j, p2 in enumerate(norm_prefixes):
                if i == j:
                    continue
                if p2.startswith(p1):
                    # 严格：前缀包含不允许（例如 '!' 与 '!!'）
                    LOG.error(f"消息前缀冲突: '{p1}' 与 '{p2}' 存在包含关系")
                    raise ValueError(f"prefix conflict: {p1} vs {p2}")

        # 2) 采集命令定义（仅带 __is_command__ 的函数）
        # CommandGroup.get_all_commands 返回 {path_tuple: func}

        # TODO: 这里的原始逻辑就是只处理了command_registry中的所有命令与别称，不确定是否需要修改
        command_map = command_registry.get_all_commands()
        alias_map = command_registry.get_all_aliases()

        # 过滤：仅保留被标记为命令的函数（装饰器会设置 __is_command__）
        filtered_commands: Dict[Tuple[str, ...], CommandSpec] = {}
        for path, command in command_map.items():
            if getattr(command.func, "__is_command__", False):
                filtered_commands[path] = command

        filtered_aliases: Dict[Tuple[str, ...], CommandSpec] = {}
        for path, command in alias_map.items():
            if getattr(command.func, "__is_command__", False):
                filtered_aliases[path] = command

        # 3) 交给 resolver 构建并做冲突检测
        self._resolver.build_index(filtered_commands, filtered_aliases)
        LOG.debug(
            f"TriggerEngine 初始化完成：命令={len(filtered_commands)}, 别名={len(filtered_aliases)}"
        )

    async def handle_legacy_event(self, event: "NcatBotEvent") -> bool:
        """处理通知和请求事件"""
        event_data: "BaseEvent" = event.data
        if event_data.post_type == "notice":
            for func in legacy_registry._notice_event:
                await self._execute_function(func, event_data)
        elif event_data.post_type == "request":
            for func in legacy_registry._request_event:
                await self._execute_function(func, event_data)
        return True

    def _find_plugin_for_function(self, func: Callable) -> "NcatBotPlugin":
        """查找函数所属的插件"""
        # 缓存查找结果
        if func in self.func_plugin_map:
            return self.func_plugin_map[func]

        # 遍历所有插件查找函数归属
        plugins = self.list_plugins(obj=True)
        for plugin in plugins:
            plugin_class = plugin.__class__
            if func in plugin_class.__dict__.values():
                self.func_plugin_map[func] = plugin
                return plugin

        return None

    def clear(self):
        """清理缓存"""
        self.func_plugin_map.clear()
        self._initialized = False
        self._resolver.clear()
