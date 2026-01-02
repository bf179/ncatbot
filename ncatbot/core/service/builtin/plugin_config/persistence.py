"""
插件配置持久化

负责配置的加载、保存和精细化持久化操作。
"""

from typing import Any, Dict
from pathlib import Path
import yaml
import aiofiles
import asyncio

from ncatbot.utils import get_log

LOG = get_log("PluginConfigPersistence")


class ConfigPersistence:
    """配置持久化处理器"""
    
    def __init__(self, config_path: Path):
        self._config_path = config_path
    
    # -------------------------------------------------------------------------
    # 精细化保存（单项/多项）
    # -------------------------------------------------------------------------
    
    def atomic_save_item(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        name: str,
        deleted: bool = False,
    ) -> None:
        """原子保存单个配置项"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._save_item_async(configs, plugin_name, name, deleted)
            )
        except RuntimeError:
            self._save_item_sync(configs, plugin_name, name, deleted)
    
    def atomic_save_items(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        names: list,
    ) -> None:
        """原子保存多个配置项"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._save_items_async(configs, plugin_name, names))
        except RuntimeError:
            self._save_items_sync(configs, plugin_name, names)
    
    # -------------------------------------------------------------------------
    # 同步操作
    # -------------------------------------------------------------------------
    
    def _save_item_sync(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        name: str,
        deleted: bool = False,
    ) -> None:
        """同步保存单个配置项"""
        try:
            existing_data = self._load_existing_data_sync()
            self._ensure_plugin_config_structure(existing_data, plugin_name)
            
            if deleted:
                existing_data["plugin_config"][plugin_name].pop(name, None)
            else:
                existing_data["plugin_config"][plugin_name][name] = configs[plugin_name][name]
            
            self._write_data_sync(existing_data)
            LOG.debug(f"配置项 {plugin_name}.{name} 已同步保存")
        except Exception as e:
            LOG.error(f"同步保存配置项 {plugin_name}.{name} 失败: {e}")
    
    def _save_items_sync(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        names: list,
    ) -> None:
        """同步保存多个配置项"""
        try:
            existing_data = self._load_existing_data_sync()
            self._ensure_plugin_config_structure(existing_data, plugin_name)
            
            for name in names:
                if name in configs.get(plugin_name, {}):
                    existing_data["plugin_config"][plugin_name][name] = configs[plugin_name][name]
            
            self._write_data_sync(existing_data)
            LOG.debug(f"插件 {plugin_name} 的 {len(names)} 个配置项已同步保存")
        except Exception as e:
            LOG.error(f"同步保存插件 {plugin_name} 配置项失败: {e}")
    
    def save_all_sync(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """同步保存所有配置"""
        try:
            existing_data = self._load_existing_data_sync()
            existing_data["plugin_config"] = configs
            self._write_data_sync(existing_data)
            LOG.debug("插件配置已同步保存")
        except Exception as e:
            LOG.error(f"同步保存插件配置失败: {e}")
    
    def _load_existing_data_sync(self) -> Dict[str, Any]:
        """同步加载现有数据"""
        if self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f.read()) or {}
        return {}
    
    def _write_data_sync(self, data: Dict[str, Any]) -> None:
        """同步写入数据（原子操作）"""
        tmp_path = self._config_path.with_suffix('.tmp')
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False))
        tmp_path.replace(self._config_path)
    
    # -------------------------------------------------------------------------
    # 异步操作
    # -------------------------------------------------------------------------
    
    async def _save_item_async(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        name: str,
        deleted: bool = False,
    ) -> None:
        """异步保存单个配置项"""
        try:
            existing_data = await self._load_existing_data_async()
            self._ensure_plugin_config_structure(existing_data, plugin_name)
            
            if deleted:
                existing_data["plugin_config"][plugin_name].pop(name, None)
            else:
                existing_data["plugin_config"][plugin_name][name] = configs[plugin_name][name]
            
            await self._write_data_async(existing_data)
            LOG.debug(f"配置项 {plugin_name}.{name} 已保存")
        except Exception as e:
            LOG.error(f"保存配置项 {plugin_name}.{name} 失败: {e}")
    
    async def _save_items_async(
        self,
        configs: Dict[str, Dict[str, Any]],
        plugin_name: str,
        names: list,
    ) -> None:
        """异步保存多个配置项"""
        try:
            existing_data = await self._load_existing_data_async()
            self._ensure_plugin_config_structure(existing_data, plugin_name)
            
            for name in names:
                if name in configs.get(plugin_name, {}):
                    existing_data["plugin_config"][plugin_name][name] = configs[plugin_name][name]
            
            await self._write_data_async(existing_data)
            LOG.debug(f"插件 {plugin_name} 的 {len(names)} 个配置项已保存")
        except Exception as e:
            LOG.error(f"保存插件 {plugin_name} 配置项失败: {e}")
    
    async def load_all(self) -> Dict[str, Dict[str, Any]]:
        """异步加载所有配置"""
        try:
            if not self._config_path.exists():
                return {}
            async with aiofiles.open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(await f.read()) or {}
            configs = data.get("plugin_config", {})
            LOG.debug(f"从配置文件加载了 {len(configs)} 个插件的配置")
            return configs
        except Exception as e:
            LOG.error(f"加载插件配置失败: {e}")
            return {}
    
    async def load_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """异步加载单个插件的配置"""
        try:
            if not self._config_path.exists():
                return {}
            async with aiofiles.open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(await f.read()) or {}
            plugin_config = data.get("plugin_config", {}).get(plugin_name, {})
            LOG.debug(f"从配置文件加载了插件 {plugin_name} 的配置")
            return plugin_config
        except Exception as e:
            LOG.error(f"加载插件 {plugin_name} 配置失败: {e}")
            return {}
    
    async def save_all(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """异步保存所有配置"""
        try:
            existing_data = await self._load_existing_data_async()
            existing_data["plugin_config"] = configs
            await self._write_data_async(existing_data)
            LOG.debug("插件配置已保存")
        except Exception as e:
            LOG.error(f"保存插件配置失败: {e}")
    
    async def _load_existing_data_async(self) -> Dict[str, Any]:
        """异步加载现有数据"""
        if self._config_path.exists():
            async with aiofiles.open(self._config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(await f.read()) or {}
        return {}
    
    async def _write_data_async(self, data: Dict[str, Any]) -> None:
        """异步写入数据（原子操作）"""
        tmp_path = self._config_path.with_suffix('.tmp')
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
            await f.write(yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False))
        tmp_path.replace(self._config_path)
    
    # -------------------------------------------------------------------------
    # 辅助方法
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _ensure_plugin_config_structure(data: Dict[str, Any], plugin_name: str) -> None:
        """确保 plugin_config 结构存在"""
        if "plugin_config" not in data:
            data["plugin_config"] = {}
        if plugin_name not in data["plugin_config"]:
            data["plugin_config"][plugin_name] = {}
