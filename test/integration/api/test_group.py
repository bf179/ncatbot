"""
群组相关 API 测试用例
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_case, TestCase
from api.base import APITestSuite


class GroupAPITests(APITestSuite):
    """群组相关 API 测试"""

    suite_name = "Group API"
    suite_description = "测试群组信息、成员管理等 API"

    # =========================================================================
    # 群信息查询
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取群列表",
        description="获取 Bot 加入的所有群列表",
        category="group",
        api_endpoint="/get_group_list",
        expected="返回群列表，每个群包含 group_id、group_name 等信息",
        tags=["query"],
    )
    async def test_get_group_list(api, config):
        """获取群列表"""
        result = await api.get_group_list()
        sample = result[:5] if len(result) > 5 else result
        return {
            "total_count": len(result),
            "sample": [
                {
                    "group_id": g.get("group_id"),
                    "group_name": g.get("group_name"),
                    "member_count": g.get("member_count"),
                }
                for g in sample
            ],
        }

    @staticmethod
    @test_case(
        name="获取群信息",
        description="获取指定群的详细信息",
        category="group",
        api_endpoint="/get_group_info",
        expected="返回群的详细信息，包括名称、人数、创建时间等",
        tags=["query"],
        requires_input=True,
    )
    async def test_get_group_info(api, config):
        """获取群信息"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        result = await api.get_group_info(group_id=int(target_group))
        return result

    @staticmethod
    @test_case(
        name="获取群成员列表",
        description="获取指定群的成员列表",
        category="group",
        api_endpoint="/get_group_member_list",
        expected="返回群成员列表，包含 user_id、nickname、role 等",
        tags=["query", "member"],
        requires_input=True,
    )
    async def test_get_group_member_list(api, config):
        """获取群成员列表"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        result = await api.get_group_member_list(group_id=int(target_group))
        sample = result[:5] if len(result) > 5 else result
        return {
            "total_count": len(result),
            "sample": [
                {
                    "user_id": m.get("user_id"),
                    "nickname": m.get("nickname"),
                    "card": m.get("card"),
                    "role": m.get("role"),
                }
                for m in sample
            ],
        }

    @staticmethod
    @test_case(
        name="获取群成员信息",
        description="获取指定群成员的详细信息",
        category="group",
        api_endpoint="/get_group_member_info",
        expected="返回成员详细信息，包括入群时间、最后发言时间等",
        tags=["query", "member"],
        requires_input=True,
    )
    async def test_get_group_member_info(api, config):
        """获取群成员信息"""
        target_group = config.get("target_group")
        target_user = config.get("target_user")

        if not target_group:
            target_group = input("请输入目标群号: ")
        if not target_user:
            target_user = input("请输入目标成员 QQ 号: ")

        result = await api.get_group_member_info(
            group_id=int(target_group),
            user_id=int(target_user),
        )
        return result

    # =========================================================================
    # 群管理操作（需要管理员权限）
    # =========================================================================

    @staticmethod
    @test_case(
        name="设置群名片",
        description="设置指定群成员的群名片",
        category="group",
        api_endpoint="/set_group_card",
        expected="成功设置群名片，可在群成员列表中验证",
        tags=["admin", "member"],
        requires_input=True,
    )
    async def test_set_group_card(api, config):
        """设置群名片"""
        target_group = config.get("target_group")
        target_user = config.get("target_user")

        if not target_group:
            target_group = input("请输入目标群号: ")
        if not target_user:
            target_user = input("请输入目标成员 QQ 号: ")

        new_card = input("请输入新的群名片 (留空测试清空名片): ") or ""

        await api.set_group_card(
            group_id=int(target_group),
            user_id=int(target_user),
            card=new_card,
        )
        return {
            "group_id": target_group,
            "user_id": target_user,
            "new_card": new_card or "(已清空)",
        }

    @staticmethod
    @test_case(
        name="群组禁言",
        description="禁言指定群成员（需要管理员权限）",
        category="group",
        api_endpoint="/set_group_ban",
        expected="目标成员被禁言，无法发言",
        tags=["admin", "ban"],
        requires_input=True,
    )
    async def test_set_group_ban(api, config):
        """群组禁言"""
        target_group = config.get("target_group")
        target_user = config.get("target_user")

        if not target_group:
            target_group = input("请输入目标群号: ")
        if not target_user:
            target_user = input("请输入要禁言的成员 QQ 号: ")

        duration = input("请输入禁言时长(秒, 0=解除禁言, 默认60): ") or "60"

        await api.set_group_ban(
            group_id=int(target_group),
            user_id=int(target_user),
            duration=int(duration),
        )
        return {
            "group_id": target_group,
            "user_id": target_user,
            "duration": duration,
            "action": "ban" if int(duration) > 0 else "unban",
        }

    @staticmethod
    @test_case(
        name="全员禁言",
        description="开启或关闭群全员禁言",
        category="group",
        api_endpoint="/set_group_whole_ban",
        expected="群全员禁言状态改变",
        tags=["admin", "ban"],
        requires_input=True,
    )
    async def test_set_group_whole_ban(api, config):
        """全员禁言"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        enable = input("开启全员禁言? (y/n, 默认n): ").lower() == "y"

        await api.set_group_whole_ban(
            group_id=int(target_group),
            enable=enable,
        )
        return {
            "group_id": target_group,
            "whole_ban": enable,
        }

    # =========================================================================
    # 群公告
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取群公告",
        description="获取指定群的公告列表",
        category="group",
        api_endpoint="/_get_group_notice",
        expected="返回群公告列表",
        tags=["notice"],
        requires_input=True,
    )
    async def test_get_group_notice(api, config):
        """获取群公告"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        result = await api._get_group_notice(group_id=int(target_group))
        return {
            "count": len(result) if isinstance(result, list) else "unknown",
            "sample": result[:2] if isinstance(result, list) else result,
        }

    @staticmethod
    @test_case(
        name="发送群公告",
        description="发送一条群公告（需要管理员权限）",
        category="group",
        api_endpoint="/_send_group_notice",
        expected="群公告发送成功，可在群公告列表查看",
        tags=["admin", "notice"],
        requires_input=True,
    )
    async def test_send_group_notice(api, config):
        """发送群公告"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        content = input("请输入公告内容: ") or "[NcatBot 集成测试] 测试公告"

        await api._send_group_notice(
            group_id=int(target_group),
            content=content,
        )
        return {
            "group_id": target_group,
            "content": content,
        }
