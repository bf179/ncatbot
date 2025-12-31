"""
消息路由服务

基于 NapCatWebSocket，负责：
- 区分 API 响应和事件
- 将响应分发给等待的请求
- 将事件转发给事件处理器
"""

import asyncio
import uuid
from typing import Dict, Optional, Callable, Awaitable
from threading import Lock
from queue import Queue

from ..base import BaseService
from ncatbot.core.adapter.nc import NapCatWebSocket
from ncatbot.utils import get_log

LOG = get_log("MessageRouter")


class MessageRouter(BaseService):
    """
    消息路由服务
    
    职责：
    - 管理 NapCatWebSocket 连接
    - 区分收到的消息是 API 响应（有 echo）还是事件
    - 响应分发给等待的请求
    - 事件转发给事件处理器
    
    提供 send(action, params) -> response 接口供 BotAPI 使用。
    """
    
    name = "message_router"
    description = "消息路由服务"
    
    def __init__(
        self, 
        uri: Optional[str] = None,
        event_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
        **config
    ):
        """
        Args:
            uri: WebSocket URI，不提供则从配置读取
            event_callback: 收到事件时的回调
        """
        super().__init__(**config)
        self._uri = uri
        self._event_callback = event_callback
        
        # 底层 WebSocket 连接
        self._ws: Optional[NapCatWebSocket] = None
        
        # 响应等待队列
        self._pending: Dict[str, Queue] = {}
        self._lock = Lock()
    
    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    
    async def on_load(self) -> None:
        """加载服务 - 建立连接"""
        self._ws = NapCatWebSocket(
            uri=self._uri,
            message_callback=self._on_message,
        )
        await self._ws.connect()
        LOG.info("消息路由服务已加载")
    
    async def on_close(self) -> None:
        """关闭服务"""
        with self._lock:
            self._pending.clear()
        
        if self._ws:
            await self._ws.disconnect()
            self._ws = None
        
        LOG.info("消息路由服务已关闭")
    
    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._ws is not None and self._ws.connected
    
    @property
    def websocket(self) -> Optional[NapCatWebSocket]:
        """获取底层 WebSocket 连接（供 PreUploadService 等使用）"""
        return self._ws
    
    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """设置事件回调"""
        self._event_callback = callback
    
    async def send(
        self, 
        action: str, 
        params: Optional[dict] = None, 
        timeout: float = 300.0
    ) -> dict:
        """
        发送 API 请求并等待响应
        
        Args:
            action: API 动作名
            params: 请求参数
            timeout: 超时时间（秒）
            
        Returns:
            API 响应字典
        """
        if not self._ws:
            raise ConnectionError("服务未连接")
        
        echo = str(uuid.uuid4())
        queue: Queue = Queue(maxsize=1)
        
        with self._lock:
            self._pending[echo] = queue
        
        try:
            await self._ws.send({
                "action": action.replace("/", ""),
                "params": params or {},
                "echo": echo,
            })
            return await asyncio.to_thread(queue.get, timeout=timeout)
        finally:
            with self._lock:
                self._pending.pop(echo, None)
    
    def start_listening(self):
        """启动消息监听"""
        if self._ws:
            return self._ws.start_listening()
    
    # ------------------------------------------------------------------
    # 消息处理
    # ------------------------------------------------------------------
    
    async def _on_message(self, data: dict) -> None:
        """
        处理收到的消息
        
        区分响应和事件，分别处理。
        """
        if "echo" in data:
            # API 响应 - 分发给等待的请求
            self._dispatch_response(data)
        else:
            # 事件 - 转发给事件处理器
            if self._event_callback:
                await self._event_callback(data)
    
    def _dispatch_response(self, data: dict) -> None:
        """分发 API 响应"""
        with self._lock:
            echo = data.get("echo")
            if echo:
                queue = self._pending.get(echo)
                if queue:
                    queue.put(data)
