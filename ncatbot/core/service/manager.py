"""
服务管理器

负责服务的注册、加载、卸载。
"""

from typing import Any, Dict, List, Optional, Type
from ncatbot.utils import get_log
from .base import BaseService

LOG = get_log("ServiceManager")


class ServiceManager:
    """
    服务管理器
    
    管理所有服务的生命周期，提供服务的注册、加载、卸载、获取等功能。
    """
    
    def __init__(self):
        """初始化服务管理器"""
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
    
    def register(self, service_class: Type[BaseService], **config: Any) -> None:
        """注册服务类"""
        temp = service_class(**config)
        name = temp.name
        
        self._service_classes[name] = service_class
        self._service_configs[name] = config
    
    async def load(self, service_name: str) -> BaseService:
        """加载服务"""
        if service_name in self._services:
            return self._services[service_name]
        
        if service_name not in self._service_classes:
            raise KeyError(f"服务 {service_name} 未注册")
        
        service = self._service_classes[service_name](**self._service_configs[service_name])
        await service._load()
        self._services[service_name] = service
        return service
    
    async def unload(self, service_name: str) -> None:
        """卸载服务"""
        if service_name not in self._services:
            return
        
        await self._services[service_name]._close()
        del self._services[service_name]
    
    async def load_all(self) -> None:
        """加载所有已注册的服务"""
        for name in self._service_classes:
            if name not in self._services:
                await self.load(name)
    
    async def close_all(self) -> None:
        """关闭所有已加载的服务"""
        for name in list(self._services.keys()):
            await self.unload(name)
    
    def get(self, service_name: str) -> Optional[BaseService]:
        """获取服务实例"""
        return self._services.get(service_name)
    
    def has(self, service_name: str) -> bool:
        """检查服务是否已加载"""
        return service_name in self._services
    
    def list_services(self) -> List[str]:
        """列出所有已加载的服务名称"""
        return list(self._services.keys())
