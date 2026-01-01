"""
配置混入类

提供插件配置的便捷接口，实际配置管理委托给 PluginConfigService。
此类仅作为接口层，所有配置操作都通过服务完成。

采用"严格的写时保存"策略：
- 每次写配置时立即持久化
- self.config 是只读字典，不允许直接修改
- 必须通过 set_config() 或 self.config.update() 方法更新
"""

from typing import Any, Dict, Union, Callable, Optional, TYPE_CHECKING
from ncatbot.utils import get_log
from ..base_plugin import BasePlugin

if TYPE_CHECKING:
    from ncatbot.core.service import ServiceManager
    from ncatbot.core.service.builtin import ConfigItem, PluginConfigService, PluginConfig

LOG = get_log("ConfigMixin")


class ConfigMixin(BasePlugin):
    """
    配置混入类
    
    为插件提供便捷的配置注册和访问接口。
    所有配置操作都委托给 PluginConfigService，此类仅提供接口封装。
    
    配置策略：
    - self.config 是只读字典（PluginConfig），禁止直接赋值
    - 读取配置：self.config["key"]
    - 写入配置：self.set_config("key", value) 或 self.config.update("key", value)
    - 每次写入会触发原子保存到文件
    """
    
    
    def get_registered_configs(self) -> Dict[str, "ConfigItem"]:
        """获取本插件所有已注册的配置项"""
        return self.config_service.get_registered_configs(self.name)

    def register_config(
        self,
        name: str,
        default_value: Any = None,
        description: str = "",
        value_type: type = str,
        metadata: Optional[Dict[str, Any]] = None,
        on_change: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        """
        注册一个配置项
        
        注册后配置会自动添加到 self.config 中，无需手动同步。
        
        Args:
            name: 配置项名称
            default_value: 默认值（必须）
            description: 配置描述
            value_type: 值类型（支持 str, int, float, bool, dict, list）
            metadata: 额外元数据
            on_change: 值变更回调
            
        Raises:
            TypeError: 如果未提供 default_value
            ValueError: 如果配置项已存在
        """
        # 兼容旧版参数
        if "default" in kwargs:
            default_value = kwargs["default"]

        if default_value is None:
            raise TypeError(
                "ConfigMixin.register_config() missing 1 required positional argument: 'default_value'"
            )

        LOG.debug(f"插件 {self.name} 注册配置 {name}")
        
        self.config_service.register_config(
            plugin_name=self.name,
            name=name,
            default_value=default_value,
            description=description,
            value_type=value_type,
            metadata=metadata,
            on_change=on_change,
        )
        self.config._sync_from_service()
    
    def set_config(self, name: str, value: Any) -> tuple:
        """
        设置配置值（触发原子保存）
        
        此方法会立即将配置写入文件。
        
        Args:
            name: 配置项名称
            value: 新值
            
        Returns:
            (old_value, new_value) 元组
        """
        return self.config.update(name, value)
