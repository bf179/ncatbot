"""
预上传专用 WebSocket 连接

为预上传服务提供独立的 WebSocket 连接，负责发送上传请求并等待响应。
"""

import asyncio
import json
import uuid
from typing import Optional, Dict
from threading import Lock
from queue import Queue

from ncatbot.core.adapter.nc import NapCatWebSocket
from ncatbot.utils import get_log

LOG = get_log("UploadConnection")


class UploadConnection:
    """
    预上传专用 WebSocket 连接
    
    封装 NapCatWebSocket，提供：
    - 独立的连接生命周期
    - 请求-响应配对（基于 echo）
    - 自动消息监听
    """
    
    def __init__(self, uri: Optional[str] = None):
        """
        Args:
            uri: WebSocket URI，不提供则从配置读取
        """
        self._uri = uri
        self._ws: Optional[NapCatWebSocket] = None
        
        # 响应等待队列
        self._pending: Dict[str, Queue] = {}
        self._lock = Lock()
    
    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------
    
    async def connect(self) -> None:
        """建立连接并开始监听"""
        self._ws = NapCatWebSocket(
            uri=self._uri,
            message_callback=self._on_message,
        )
        await self._ws.connect()
        self._ws.start_listening()
        LOG.debug("预上传连接已建立")
    
    async def disconnect(self) -> None:
        """关闭连接"""
        with self._lock:
            self._pending.clear()
        
        if self._ws:
            await self._ws.disconnect()
            self._ws = None
        
        LOG.debug("预上传连接已关闭")
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._ws is not None and self._ws.connected
    
    # ------------------------------------------------------------------
    # 请求发送
    # ------------------------------------------------------------------
    
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
            raise ConnectionError("预上传连接未建立")
        
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
    
    # ------------------------------------------------------------------
    # 消息处理
    # ------------------------------------------------------------------
    
    async def _on_message(self, data: dict) -> None:
        """
        处理收到的消息
        
        只关心有 echo 的响应，其他消息忽略。
        """
        echo = data.get("echo")
        
        if echo and echo in self._pending:
            with self._lock:
                queue = self._pending.get(echo)
            if queue:
                queue.put(data)
        # 没有 echo 的消息忽略（不是我们发的请求的响应）
