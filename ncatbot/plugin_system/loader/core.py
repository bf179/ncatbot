import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Type, Union

from ncatbot.utils import ncatbot_config, get_log, status

from ..base_plugin import BasePlugin
from ..event import EventBus
from ..pluginsys_err import (
    PluginDependencyError,
    PluginVersionError,
)
from ..config import config
from ..rbac import RBACManager
from ..builtin_plugin import SystemManager, UnifiedRegistryPlugin
from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version

from .importer import _ModuleImporter
from .resolver import _DependencyResolver

LOG = get_log("PluginLoader")


class PluginLoader:
    """插件加载器：负责插件的加载、卸载、重载、生命周期管理。"""

    def __init__(self, event_bus: EventBus, *, debug: bool = False) -> None:
        self.plugins: Dict[str, BasePlugin] = {}
        self.event_bus = event_bus or EventBus()
        self.rbac_manager = RBACManager(config.rbac_path)
        self._debug = debug
        self._importer = _ModuleImporter(str(ncatbot_config.plugin.plugins_dir))
        self._resolver = _DependencyResolver()

        # 将rbac_manager注册到全局状态
        status.global_access_manager = self.rbac_manager

        if debug:
            LOG.warning("插件系统已切换为调试模式")

    # -------------------- 对外 API --------------------
    async def _init_plugin_in_thread(self, plugin: BasePlugin) -> None:
        """在插件的线程中初始化"""

        def _run_init():
            # 在线程中创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 运行初始化
                loop.run_until_complete(plugin.__onload__())
            finally:
                loop.close()

        # 在插件的线程池中执行初始化
        await asyncio.get_event_loop().run_in_executor(plugin.thread_pool, _run_init)

    async def load_plugin_by_class(
        self, plugin_class: Type[BasePlugin], name: str, **kwargs
    ) -> BasePlugin:
        """
        Instantiate plugin_class and initialize it. kwargs may contain manifest-derived
        metadata and other extras; they will be forwarded to the plugin constructor.
        """
        plugin = plugin_class(
            event_bus=self.event_bus,
            debug=self._debug,
            rbac_manager=self.rbac_manager,
            plugin_loader=self,
            **kwargs,
        )
        # Ensure name is set (may be provided via manifest)
        if not getattr(plugin, "name", None):
            plugin.name = name
        # Attach meta_data if provided
        if kwargs.get("meta_data"):
            try:
                setattr(plugin, "meta_data", kwargs.get("meta_data"))
            except Exception:
                pass
        self.plugins[name] = plugin
        await self._init_plugin_in_thread(plugin)
        return plugin

    async def load_all_plugins_by_class(
        self, plugin_classes: Dict[str, tuple], **kwargs
    ) -> None:
        """从「插件类对象」加载。plugin_classes: name -> (Type[BasePlugin], manifest_dict)"""
        print(plugin_classes)
        valid_classes = {
            name: val for name, val in plugin_classes.items() if self._is_valid(val)
        }
        self._resolver.build(valid_classes)

        load_order = self._resolver.resolve()
        init_tasks = []

        for name in load_order:
            cls, manifest = valid_classes[name]
            LOG.info("加载插件「%s」", name)
            # Collect extras from manifest
            extras = {"meta_data": manifest}
            extras.update(
                {
                    k: v
                    for k, v in manifest.items()
                    if k in ("name", "version", "author", "description", "dependencies")
                }
            )
            init_tasks.append(self.load_plugin_by_class(cls, name, **extras))

        self._validate_versions()
        # 并发执行所有插件的初始化
        await asyncio.gather(*init_tasks)

    async def load_builtin_plugins(self) -> None:
        """加载内置插件。"""
        plugins = {
            "system_manager": SystemManager,
            "unified_registry": UnifiedRegistryPlugin,
        }
        for name, plg in plugins.items():
            await self.load_plugin_by_class(plg, name)
        LOG.info("已加载内置插件数 [%d]", len(self.plugins))

    async def load_plugins(self, **kwargs) -> None:
        """从目录批量加载。"""
        path = Path(ncatbot_config.plugin.plugins_dir).resolve()
        await self.load_builtin_plugins()
        if not path.exists():
            LOG.info("插件目录: %s 不存在……跳过加载插件", path)
            return

        if ncatbot_config.plugin.skip_plugin_load:
            LOG.info("跳过外部插件加载")
            return

        LOG.info("从 %s 导入插件", path)
        plugin_folder_names = self._importer.inspect_all()
        plugin_classes: Dict[str, tuple] = {}
        importer = self._importer
        for name in plugin_folder_names:
            if (
                ncatbot_config.plugin.plugin_whitelist
                and name not in ncatbot_config.plugin.plugin_whitelist
            ):
                LOG.info("插件 '%s' 不在白名单中，跳过加载", name)
                continue
            if name in ncatbot_config.plugin.plugin_blacklist:
                LOG.info("插件 '%s' 在黑名单中，跳过加载", name)
                continue
            # Determine module path based on manifest main field (package or single file)
            manifest = importer.get_manifest(name) or {}
            main_rel = manifest.get("main", "main.py")
            candidate_file = path / name / main_rel
            module_path = candidate_file if candidate_file.exists() else (path / name)
            module = importer.load_module(name, module_path)
            if not module:
                continue
            # Prefer entry_class if specified in manifest
            cls = None
            entry_class_name = manifest.get("entry_class")
            if entry_class_name:
                cls = getattr(module, entry_class_name, None)
            if not cls:
                # Fallback to auto-discover first BasePlugin subclass
                cls = self._find_plugin_class_in_module(module)
            if not cls:
                LOG.warning("在模块中未找到插件类 '%s'", name)
                continue
            plugin_classes[name] = (cls, manifest)

        await self.load_all_plugins_by_class(plugin_classes, **kwargs)
        LOG.info("已加载插件数 [%d]", len(self.plugins))

    async def load_plugin(self, name) -> BasePlugin:
        try:
            module = self._importer.load_module(
                name, Path(ncatbot_config.plugin.plugins_dir) / name
            )
            return await self.load_plugin_by_class(
                self._find_plugin_class_in_module(module), name
            )
        except Exception as e:
            LOG.error(f"尝试加载失败的插件 {name}: {e}")

    async def unload_plugin(self, name: str, **kwargs) -> bool:
        """卸载单个插件。"""
        plugin = self.plugins.get(name)
        if not plugin:
            LOG.warning("插件 '%s' 未加载，无法卸载", name)
            return False
        try:
            await plugin.__unload__(**kwargs)
            self._importer.unload_module(name)
            del self.plugins[name]
            return True
        except Exception as e:
            LOG.error("卸载插件 '%s' 时发生错误: %s", name, e)
            return False

    async def reload_plugin(self, name: str, **kwargs) -> bool:
        """重载单个插件。"""
        try:
            await self.unload_plugin(name, **kwargs)
            await self.load_plugin(name)
            LOG.info("插件 '%s' 重载成功", name)
            return True
        except Exception as e:
            LOG.error("重载插件 '%s' 失败: %s", name, e)
            return False

    async def unload_all(self, **kwargs) -> None:
        """一键异步卸载全部插件。"""
        self.rbac_manager.save(config.rbac_path)
        await asyncio.gather(
            *(self.unload_plugin(name, **kwargs) for name in list(self.plugins))
        )

    # -------------------- 查询 API --------------------
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.plugins.get(name, None)

    def get_metadata(self, name: str) -> dict:
        return self.plugins[name].meta_data

    def list_plugins(self, *, obj: bool = False) -> List[Union[str, BasePlugin]]:
        return list(self.plugins.values()) if obj else list(self.plugins.keys())

    # -------------------- 私有辅助 --------------------
    @staticmethod
    def _is_valid(cls: Type[BasePlugin]) -> bool:
        # Only accept (Type[BasePlugin], manifest) tuples
        if not isinstance(cls, tuple):
            return False
        target = cls[0]
        try:
            return issubclass(target, BasePlugin)
        except Exception:
            return False

    def _validate_versions(self) -> None:
        """检查已加载插件的版本约束。"""
        for plugin_name, constraints in self._resolver._constraints.items():
            for dep_name, constraint in constraints.items():
                dep = self.plugins.get(dep_name)
                if not dep:
                    raise PluginDependencyError(plugin_name, dep_name, constraint)
                if not SpecifierSet(constraint).contains(parse_version(dep.version)):
                    raise PluginVersionError(
                        plugin_name, dep_name, constraint, dep.version
                    )

    def _find_plugin_class_in_module(
        self, module: ModuleType
    ) -> Optional[Type[BasePlugin]]:
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, BasePlugin):
                return obj
        return None
