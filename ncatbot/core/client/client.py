"""
Bot 客户端

组合各模块，提供统一的 Bot 客户端接口。
"""

from typing import List, Type, TypeVar, TYPE_CHECKING

from ncatbot.utils import get_log, status
from ncatbot.utils.error import NcatBotError
from ncatbot.core.adapter import Adapter
from ncatbot.core.api import BotAPI

from .event_bus import EventBus
from .dispatcher import EventDispatcher
from .registry import EventRegistry
from .lifecycle import LifecycleManager

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin

T = TypeVar("T")
LOG = get_log("Client")


class BotClient(EventRegistry, LifecycleManager):
    """
    Bot 客户端
    
    架构：
    ┌─────────────────────────────────────────────────────────┐
    │                       BotClient                         │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ Adapter  │  │ EventBus │  │ Registry │  │Lifecycle│ │
    │  │(通信层)   │ │(分发中心) │ │(注册接口)  │ │(生命周期)│ │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
    │       │             │             │             │       │
    │       └─────────────┴─────────────┴─────────────┘       │
    │                         ↓                               │
    │                   EventDispatcher                       │
    │                    (解析 & 分发)                         │
    └─────────────────────────────────────────────────────────┘
    
    事件流：
    WebSocket → Adapter → Dispatcher → EventBus → Handlers/Plugins
    
    继承：
    - EventRegistry: 提供事件注册和装饰器接口
    """

    _initialized = False

    def __init__(self, only_private: bool = False, max_workers: int = 16):
        """
        初始化 Bot 客户端
        
        Args:
            only_private: 是否只处理私聊消息
            max_workers: 兼容参数，已废弃
        """
        if self._initialized:
            raise NcatBotError("BotClient 实例只能创建一次")
        self._initialized = True

        # 核心组件
        self.event_bus = EventBus()
        
        # 初始化父类 EventRegistry
        super().__init__(self.event_bus)
        
        self.adapter = Adapter()
        self.api = BotAPI(self.adapter.send)
        
        # 事件分发器
        self.dispatcher = EventDispatcher(self.event_bus, self.api)
        self.adapter.set_event_callback(self.dispatcher)
        
        # 生命周期管理器（传入 self，因为 BotClient 现在就是 EventRegistry）
        self._lifecycle = LifecycleManager(
            self.adapter, self.api, self.event_bus, self
        )
        
        # 全局状态
        status.global_api = self.api
        self._only_private = only_private
        
        # 注册内置处理器
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """注册内置处理器"""
        if not self._only_private:
            self.on_startup()(lambda e: LOG.info(f"Bot {e.self_id} 启动成功"))

    # ==================== 工具方法 ====================

    def get_registered_plugins(self) -> List["BasePlugin"]:
        """获取已注册的插件列表"""
        if self.plugin_loader:
            return list(self.plugin_loader.plugins.values())
        return []

    def get_plugin(self, plugin_type: Type[T]) -> T:
        """获取指定类型的插件"""
        for plugin in self.get_registered_plugins():
            if isinstance(plugin, plugin_type):
                return plugin
        raise ValueError(f"插件 {plugin_type.__name__} 未找到")