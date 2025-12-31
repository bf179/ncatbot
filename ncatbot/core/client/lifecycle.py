"""
生命周期管理

负责 Bot 的启动、退出和运行模式管理。
"""

import asyncio
import threading
import traceback
from typing import Callable, Union, Optional, TypedDict, TYPE_CHECKING

from typing_extensions import Unpack

from ncatbot.utils import get_log, run_coroutine, status, ncatbot_config
from ncatbot.utils.error import NcatBotError, NcatBotConnectionError
from ncatbot.core.adapter import launch_napcat_service

if TYPE_CHECKING:
    from ncatbot.core.api import BotAPI
    from ncatbot.core.service import ServiceManager, WebSocketService
    from .event_bus import EventBus
    from .registry import EventRegistry

LOG = get_log("Lifecycle")


class StartArgs(TypedDict, total=False):
    """启动参数类型定义"""
    bt_uin: Union[str, int]
    root: Optional[str]
    ws_uri: Optional[str]
    webui_uri: Optional[str]
    ws_token: Optional[str]
    webui_token: Optional[str]
    ws_listen_ip: Optional[str]
    remote_mode: Optional[bool]
    enable_webui: Optional[bool]
    enable_webui_interaction: Optional[bool]
    debug: Optional[bool]


LEGAL_ARGS = StartArgs.__annotations__.keys()


class LifecycleManager:
    """
    生命周期管理器
    
    职责：
    - Bot 启动流程
    - Bot 退出流程
    - 前台/后台运行模式
    - 插件加载器管理
    """
    
    def __init__(
        self,
        services: "ServiceManager",
        event_bus: "EventBus",
        registry: "EventRegistry",
    ):
        """
        初始化生命周期管理器
        
        Args:
            services: 服务管理器
            event_bus: 事件总线
            registry: 事件注册器
        """
        self.services = services
        self.event_bus = event_bus
        self.registry = registry
        
        self._running = False
        self.crash_flag = False
        self.plugin_loader = None
        self.api: Optional["BotAPI"] = None
        
        # 后台运行相关
        self.lock: Optional[threading.Lock] = None
        self.release_callback: Optional[Callable[[None], None]] = None

    def start(self, **kwargs: Unpack[StartArgs]):
        """
        启动 Bot
        
        流程：
        1. 验证并应用配置参数
        2. 初始化插件加载器
        3. 加载插件
        4. 启动 NapCat 服务
        5. 加载内置服务并连接 WebSocket
        """
        # 验证并应用配置
        for key, value in kwargs.items():
            if key not in LEGAL_ARGS:
                raise NcatBotError(f"非法参数: {key}")
            if value is not None:
                ncatbot_config.update_value(key, value)

        ncatbot_config.validate_config()

        # 初始化插件系统
        from ncatbot.plugin_system import PluginLoader
        self.plugin_loader = PluginLoader(self.event_bus, debug=ncatbot_config.debug)
        self._running = True

        # 加载插件
        run_coroutine(self.plugin_loader.load_plugins)

        # 启动服务
        if getattr(self, "mock_mode", False):
            self.mock_start()
        else:
            launch_napcat_service()
            try:
                asyncio.run(self._async_start())
            except NcatBotConnectionError:
                self.bot_exit()
                raise
    
    async def _async_start(self):
        """异步启动流程"""
        # 加载所有服务
        await self.services.load_all()
        
        # 获取 WebSocket 服务并设置 API
        ws_service: "WebSocketService" = self.services.get("websocket")
        
        from ncatbot.core.api import BotAPI
        from .dispatcher import EventDispatcher
        
        self.api = BotAPI(ws_service.send)
        
        # 设置事件分发器
        dispatcher = EventDispatcher(self.event_bus, self.api)
        ws_service.set_event_callback(dispatcher)
        
        # 开始监听
        await ws_service.listen()

    def bot_exit(self):
        """退出 Bot"""
        if not self._running:
            LOG.warning("Bot 未运行")
            return
        status.exit = True
        
        # 关闭所有服务
        run_coroutine(self.services.close_all)
        
        if self.plugin_loader:
            asyncio.run(self.plugin_loader.unload_all())
        LOG.info("Bot 已退出")

    def run_frontend(self, **kwargs: Unpack[StartArgs]):
        """
        前台运行（阻塞）
        
        适用于：命令行直接运行
        """
        try:
            self.start(**kwargs)
        except KeyboardInterrupt:
            self.bot_exit()

    def run_backend(self, **kwargs: Unpack[StartArgs]) -> "BotAPI":
        """
        后台运行（非阻塞）
        
        适用于：与其他程序集成
        
        Returns:
            BotAPI 实例
        """
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.start(**kwargs)
            except Exception as e:
                LOG.error(f"启动失败: {e}\n{traceback.format_exc()}")
                self.crash_flag = True
                if self.release_callback:
                    self.release_callback(None)
            finally:
                loop.close()

        self.lock = threading.Lock()
        self.lock.acquire()
        self.release_callback = lambda _: self.lock.release() # type: ignore
        self.registry.add_startup_handler(self.release_callback)

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

        if not self.lock.acquire(timeout=90):
            raise NcatBotError("启动超时")
        if self.crash_flag:
            raise NcatBotError("启动失败", log=False)
        return self.api

    def mock_start(self):
        """Mock 启动（用于测试）"""
        LOG.info("Mock 模式启动")

    # ==================== 兼容别名 ====================
    run_blocking = run_frontend
    run_non_blocking = run_backend
    run = run_frontend
