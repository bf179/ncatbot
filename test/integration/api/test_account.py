"""
账号相关 API 测试用例
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_case, TestCase
from api.base import APITestSuite


class AccountAPITests(APITestSuite):
    """账号相关 API 测试"""

    suite_name = "Account API"
    suite_description = "测试账号信息、好友管理等 API"

    # =========================================================================
    # 账号信息
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取登录信息",
        description="获取当前登录的 QQ 账号基本信息",
        category="account",
        api_endpoint="/get_login_info",
        expected="返回包含 user_id（QQ号）和 nickname（昵称）的信息",
        tags=["basic", "account"],
    )
    async def test_get_login_info(api, config):
        """获取登录信息"""
        result = await api.get_login_info()
        return {
            "user_id": result.user_id,
            "nickname": result.nickname,
        }

    @staticmethod
    @test_case(
        name="获取状态",
        description="获取 NapCat 运行状态信息",
        category="account",
        api_endpoint="/get_status",
        expected="返回包含 online 状态和 good 状态的信息",
        tags=["basic", "status"],
    )
    async def test_get_status(api, config):
        """获取状态"""
        result = await api.get_status()
        return result

    @staticmethod
    @test_case(
        name="获取版本信息",
        description="获取 NapCat 版本信息",
        category="account",
        api_endpoint="/get_version_info",
        expected="返回 app_name、app_version 等版本信息",
        tags=["basic", "version"],
    )
    async def test_get_version_info(api, config):
        """获取版本信息"""
        result = await api.get_version_info()
        return result

    # =========================================================================
    # 好友相关
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取好友列表",
        description="获取当前账号的好友列表",
        category="account",
        api_endpoint="/get_friend_list",
        expected="返回好友列表，每个好友包含 user_id、nickname 等信息",
        tags=["friend"],
    )
    async def test_get_friend_list(api, config):
        """获取好友列表"""
        result = await api.get_friend_list()
        # 返回前 5 个好友作为示例
        sample = result[:5] if len(result) > 5 else result
        return {
            "total_count": len(result),
            "sample": [
                {"user_id": f.get("user_id"), "nickname": f.get("nickname")}
                for f in sample
            ],
        }

    @staticmethod
    @test_case(
        name="获取陌生人信息",
        description="获取指定 QQ 号的用户信息",
        category="account",
        api_endpoint="/get_stranger_info",
        expected="返回用户的 user_id、nickname、sex、age 等信息",
        tags=["friend"],
        requires_input=True,
    )
    async def test_get_stranger_info(api, config):
        """获取陌生人信息"""
        target_user = config.get("target_user")
        if not target_user:
            target_user = input("请输入要查询的 QQ 号: ")

        result = await api.get_stranger_info(user_id=int(target_user))
        return result

    # =========================================================================
    # 最近联系人
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取最近联系人",
        description="获取最近的聊天联系人列表",
        category="account",
        api_endpoint="/get_recent_contact",
        expected="返回最近联系人列表",
        tags=["contact"],
    )
    async def test_get_recent_contact(api, config):
        """获取最近联系人"""
        result = await api.get_recent_contact()
        return {
            "count": len(result) if isinstance(result, list) else "unknown",
            "sample": result[:3] if isinstance(result, list) and len(result) > 0 else result,
        }
