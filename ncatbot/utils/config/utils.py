import random
import string
from re import search
from typing import Any

URI_SPECIAL_CHARS = "-_.~!()*"


def strong_password_check(password: str) -> bool:
    """检查密码强度：包含数字、大小写字母、特殊符号，至少 12 位。"""
    patterns = [r"\d", "[a-z]", "[A-Z]", f"[{URI_SPECIAL_CHARS}]"]
    return len(password) >= 12 and all(
        search(pattern, password) for pattern in patterns
    )


def generate_strong_token(length: int = 16) -> str:
    """生成满足强度策略的随机密码, 需要避免 uri 禁止的符号"""
    all_chars = string.ascii_letters + string.digits + URI_SPECIAL_CHARS
    while True:
        password = "".join(random.choice(all_chars) for _ in range(length))
        if strong_password_check(password):
            return password

