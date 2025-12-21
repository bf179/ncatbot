import sys
import importlib
import toml
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional

from ncatbot.utils import get_log

from ..config import config
from ..packhelper import PackageHelper

LOG = get_log("ModuleImporter")
_AUTO_INSTALL = config.auto_install_pip_pack


class _ModuleImporter:
    """把「目录->模块对象」的细节收敛到这里，方便做单元测试。"""

    def __init__(self, directory: str):
        self.directory = Path(directory).resolve()
        # 存储每个插件解析出的 manifest 数据： name -> dict
        self._manifests: Dict[str, dict] = {}

    def inspect_all(self) -> List[str]:
        """返回所有符合 manifest-only 约定的插件目录名列表。"""
        plugin_folder_names: List[str] = []
        for entry in self.directory.iterdir():
            name = entry.stem
            # 仅识别包含 manifest.toml 的插件目录（manifest-only 约定）
            manifest_path = entry / "manifest.toml"
            if entry.is_dir() and manifest_path.exists():
                try:
                    manifest = toml.load(manifest_path)
                    # 基本校验：必须包含 name/version/main
                    if (
                        not manifest.get("name")
                        or not manifest.get("version")
                        or not manifest.get("main")
                    ):
                        LOG.warning("插件 %s 的 manifest 缺少必填字段，跳过", entry)
                        continue
                    plugin_folder_names.append(entry.name)
                    self._manifests[entry.name] = manifest
                except Exception:
                    LOG.exception("解析 manifest 失败: %s", manifest_path)
                    continue
            else:
                LOG.debug("跳过非插件文件/目录或缺少 manifest: %s", entry)
        return plugin_folder_names

    def unload_module(self, name: str) -> bool:
        """卸载指定模块及其所有子模块"""
        if not name or not isinstance(name, str):
            LOG.warning("无效的模块名称: %s", name)
            return False

        modules_to_remove = [
            module_name
            for module_name in list(sys.modules.keys())
            if module_name == name or module_name.startswith(f"{name}.")
        ]

        if not modules_to_remove:
            LOG.debug("模块 %s 未加载，无需卸载", name)
            return True

        removed_count = 0
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
                removed_count += 1
                LOG.debug("已卸载模块: %s", module_name)
            except KeyError:
                pass

        LOG.info("成功卸载模块 %s (共 %d 个模块)", name, removed_count)
        return True

    def load_module(self, name: str, path: Path) -> Optional[ModuleType]:
        """加载模块并自动处理依赖（path 可以是目录或文件）。"""
        if not name or not path:
            LOG.error("模块名称或路径无效: name=%s, path=%s", name, path)
            return None
        if not path.exists():
            LOG.error("模块路径不存在: %s", path)
            return None
        try:
            # 清理旧版本，确保干净加载环境
            self.unload_module(name)

            # 自动安装依赖
            LOG.debug("正在检查并安装模块 %s 的依赖", name)
            self._maybe_install_deps(path)

            # 执行导入
            LOG.info("正在加载模块: %s from %s", name, path)
            module = self._import_single(name, path)
            LOG.info("模块 %s 加载成功", name)
            return module

        except Exception as e:
            LOG.error("加载模块 %s 失败: %s", name, e, exc_info=True)
            # 清理残留
            self.unload_module(name)
            return None

    def _import_single(self, name: str, path: Path) -> ModuleType:
        try:
            original_sys_path = sys.path.copy()
            sys.path.insert(0, str(path.parent))
            if path.is_dir():
                return importlib.import_module(name)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            LOG.info("成功导入插件文件: %s", name)
            return module
        except Exception as e:
            LOG.error("导入模块 %s 时出错: %s", name, e)
            raise
        finally:
            sys.path = original_sys_path

    def get_manifest(self, name: str) -> Optional[dict]:
        """返回已解析的 manifest（若 inspect_all 已解析过）。"""
        return self._manifests.get(name)

    def _maybe_install_deps(self, plugin_path: Path) -> None:
        if not _AUTO_INSTALL:
            return

        def ensure_req_from_requirements():
            req_file = (
                plugin_path / "requirements.txt"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".requirements.txt")
            )
            if not req_file.exists():
                return

            for line in req_file.read_text(encoding="utf-8").splitlines():
                req = line.strip()
                if not req or req.startswith("#") or req.startswith("-"):
                    continue
                self._ensure_package(req)

        def ensure_req_from_pyproject():
            pyproject = (
                plugin_path / "pyproject.toml"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".pyproject.toml")
            )
            if not pyproject.exists():
                return
            data = toml.load(pyproject)
            requires = data.get("project", {}).get("dependencies", [])
            for req in requires:
                self._ensure_package(req)

        ensure_req_from_pyproject()
        ensure_req_from_requirements()

    def _ensure_package(self, req: str) -> None:
        """检查包是否存在，不存在则安装。"""
        PackageHelper.ensure(req)
