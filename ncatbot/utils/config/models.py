"""配置数据模型层 - 使用 Pydantic 定义配置结构和校验逻辑。"""

import os
import urllib.parse
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .utils import strong_password_check, generate_strong_password


# ==================== 常量 ====================

DEFAULT_WS_TOKEN = "napcat_ws"
DEFAULT_WEBUI_TOKEN = "napcat_webui"
DEFAULT_BOT_UIN = "123456"
DEFAULT_ROOT = "123456"


# ==================== 子配置模型 ====================


class PluginConfig(BaseModel):
    """插件配置。"""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    plugins_dir: str = Field(default="plugins")
    plugin_whitelist: List[str] = Field(default_factory=list)
    plugin_blacklist: List[str] = Field(default_factory=list)
    load_plugin: bool = False

    @field_validator("plugins_dir")
    @classmethod
    def _validate_plugins_dir(cls, v: str) -> str:
        return v if v else "plugins"

    def ensure_dir_exists(self) -> None:
        """确保插件目录存在。"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)


class NapCatConfig(BaseModel):
    """NapCat 客户端配置。"""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    ws_uri: str = "ws://localhost:3001"
    ws_token: str = DEFAULT_WS_TOKEN
    ws_listen_ip: str = "localhost"
    webui_uri: str = "http://localhost:6099"
    webui_token: str = DEFAULT_WEBUI_TOKEN
    enable_webui: bool = True
    enable_update_check: bool = False
    stop_napcat: bool = False
    remote_mode: bool = False

    @field_validator("ws_uri")
    @classmethod
    def _validate_ws_uri(cls, v: str) -> str:
        if not v:
            return "ws://localhost:3001"
        if not (v.startswith("ws://") or v.startswith("wss://")):
            return f"ws://{v}"
        return v

    @field_validator("webui_uri")
    @classmethod
    def _validate_webui_uri(cls, v: str) -> str:
        if not v:
            return "http://localhost:6099"
        if not (v.startswith("http://") or v.startswith("https://")):
            return f"http://{v}"
        return v

    @property
    def ws_host(self) -> Optional[str]:
        """WebSocket 主机地址。"""
        return urllib.parse.urlparse(self.ws_uri).hostname

    @property
    def ws_port(self) -> Optional[int]:
        """WebSocket 端口。"""
        return urllib.parse.urlparse(self.ws_uri).port

    @property
    def webui_host(self) -> Optional[str]:
        """WebUI 主机地址。"""
        return urllib.parse.urlparse(self.webui_uri).hostname

    @property
    def webui_port(self) -> Optional[int]:
        """WebUI 端口。"""
        return urllib.parse.urlparse(self.webui_uri).port

    def to_dict(self) -> dict:
        """导出为字典，排除计算属性。"""
        return self.model_dump()

    def get_issues(self) -> List[str]:
        """
        返回问题列表。
        """
        return self.get_security_issues()

    def get_security_issues(self, auto_fix: bool = True) -> List[str]:
        """
        返回安全性问题列表
        Args:
            auto_fix: 是否自动修复弱密码（仅限默认值）
        """
        issues = []
        can_auto_fix = auto_fix

        # WS Token 检查
        if self.ws_listen_ip == "0.0.0.0" and not strong_password_check(self.ws_token):
            if self.ws_token != DEFAULT_WS_TOKEN:
                can_auto_fix = False
                issues.append("WS 令牌强度不足")

        # WebUI Token 检查
        if self.enable_webui and not strong_password_check(self.webui_token):
            if self.webui_token != DEFAULT_WEBUI_TOKEN:
                can_auto_fix = False
                issues.append("WebUI 令牌强度不足")

        if can_auto_fix:
            self.fix_security_issues()
            return []
        
        return issues

    def fix_security_issues(self) -> None:
        self.ws_token = generate_strong_password()
        self.webui_token = generate_strong_password()

# ==================== 主配置模型 ====================


class Config(BaseModel):
    """主配置模型。"""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    napcat: NapCatConfig = Field(default_factory=NapCatConfig)
    plugin: PluginConfig = Field(default_factory=PluginConfig)

    bot_uin: str = DEFAULT_BOT_UIN
    root: str = DEFAULT_ROOT
    debug: bool = False
    enable_webui_interaction: bool = True
    github_proxy: Optional[str] = Field(default_factory=lambda: os.getenv("GITHUB_PROXY"))
    check_ncatbot_update: bool = True
    skip_ncatbot_install_check: bool = False
    websocket_timeout: int = 15

    @field_validator("bot_uin", "root", mode="before")
    @classmethod
    def _coerce_to_str(cls, v) -> str:
        return str(v)

    @field_validator("websocket_timeout")
    @classmethod
    def _validate_timeout(cls, v: int) -> int:
        return max(1, v)

    def is_local(self) -> bool:
        """NapCat 是否为本地服务。"""
        return self.napcat.ws_host in ("localhost", "127.0.0.1")

    def is_default_uin(self) -> bool:
        """是否使用默认 QQ 号。"""
        return self.bot_uin == DEFAULT_BOT_UIN

    def is_default_root(self) -> bool:
        """是否使用默认管理员 QQ 号。"""
        return self.root == DEFAULT_ROOT

    def to_dict(self) -> dict:
        """导出为字典，用于保存到文件。"""
        return self.model_dump(exclude_none=True)


