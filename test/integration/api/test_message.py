"""
消息相关 API 测试用例
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_case, TestCase
from api.base import APITestSuite


class MessageAPITests(APITestSuite):
    """消息相关 API 测试"""

    suite_name = "Message API"
    suite_description = "测试消息发送、撤回、获取等 API"

    # =========================================================================
    # 私聊消息
    # =========================================================================

    @staticmethod
    @test_case(
        name="发送私聊文本消息",
        description="向指定用户发送纯文本私聊消息",
        category="message",
        api_endpoint="/send_private_msg",
        expected="返回 message_id，目标用户应收到消息",
        tags=["private", "text"],
        requires_input=True,
    )
    async def test_send_private_text(api, config):
        """发送私聊文本消息"""
        target_user = config.get("target_user")
        if not target_user:
            target_user = input("请输入目标用户 QQ 号: ")

        result = await api.send_private_msg(
            user_id=int(target_user),
            message="[NcatBot 集成测试] 私聊文本消息测试",
        )
        return {
            "message_id": result.get("message_id"),
            "target_user": target_user,
            "content": "[NcatBot 集成测试] 私聊文本消息测试",
        }

    # =========================================================================
    # 群聊消息
    # =========================================================================

    @staticmethod
    @test_case(
        name="发送群聊文本消息",
        description="向指定群发送纯文本群消息",
        category="message",
        api_endpoint="/send_group_msg",
        expected="返回 message_id，群成员应能看到消息",
        tags=["group", "text"],
        requires_input=True,
    )
    async def test_send_group_text(api, config):
        """发送群聊文本消息"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        result = await api.send_group_msg(
            group_id=int(target_group),
            message="[NcatBot 集成测试] 群聊文本消息测试",
        )
        return {
            "message_id": result.get("message_id"),
            "target_group": target_group,
            "content": "[NcatBot 集成测试] 群聊文本消息测试",
        }

    @staticmethod
    @test_case(
        name="发送群聊 @ 消息",
        description="向指定群发送带 @ 的消息",
        category="message",
        api_endpoint="/send_group_msg",
        expected="返回 message_id，消息应包含 @ 效果",
        tags=["group", "at"],
        requires_input=True,
    )
    async def test_send_group_at(api, config):
        """发送群聊 @ 消息"""
        target_group = config.get("target_group")
        target_user = config.get("target_user")

        if not target_group:
            target_group = input("请输入目标群号: ")
        if not target_user:
            target_user = input("请输入要 @ 的用户 QQ 号: ")

        # 使用 CQ 码格式
        message = f"[CQ:at,qq={target_user}] [NcatBot 集成测试] @ 消息测试"

        result = await api.send_group_msg(
            group_id=int(target_group),
            message=message,
        )
        return {
            "message_id": result.get("message_id"),
            "target_group": target_group,
            "at_user": target_user,
        }

    # =========================================================================
    # 消息查询
    # =========================================================================

    @staticmethod
    @test_case(
        name="获取消息详情",
        description="根据 message_id 获取消息详情",
        category="message",
        api_endpoint="/get_msg",
        expected="返回消息的完整信息，包括发送者、内容、时间等",
        tags=["query"],
        requires_input=True,
    )
    async def test_get_msg(api, config):
        """获取消息详情"""
        message_id = config.get("last_message_id")
        if not message_id:
            message_id = input("请输入要查询的 message_id: ")

        result = await api.get_msg(message_id=int(message_id))
        return result

    @staticmethod
    @test_case(
        name="获取历史消息",
        description="获取指定群的历史消息记录",
        category="message",
        api_endpoint="/get_group_msg_history",
        expected="返回消息历史列表",
        tags=["query", "history"],
        requires_input=True,
    )
    async def test_get_group_msg_history(api, config):
        """获取群历史消息"""
        target_group = config.get("target_group")
        if not target_group:
            target_group = input("请输入目标群号: ")

        result = await api.get_group_msg_history(
            group_id=int(target_group),
            count=5,
        )

        messages = result.get("messages", [])
        return {
            "count": len(messages),
            "sample": [
                {
                    "message_id": m.get("message_id"),
                    "sender": m.get("sender", {}).get("nickname"),
                    "content": str(m.get("message", ""))[:50],
                }
                for m in messages[:3]
            ],
        }

    # =========================================================================
    # 消息操作
    # =========================================================================

    @staticmethod
    @test_case(
        name="撤回消息",
        description="撤回指定的消息",
        category="message",
        api_endpoint="/delete_msg",
        expected="消息被成功撤回，不再可见",
        tags=["operation"],
        requires_input=True,
    )
    async def test_delete_msg(api, config):
        """撤回消息"""
        message_id = config.get("last_message_id")
        if not message_id:
            message_id = input("请输入要撤回的 message_id: ")

        await api.delete_msg(message_id=int(message_id))
        return {
            "message_id": message_id,
            "action": "deleted",
        }

    @staticmethod
    @test_case(
        name="标记消息已读",
        description="将所有消息标记为已读",
        category="message",
        api_endpoint="/_mark_all_as_read",
        expected="所有未读消息被标记为已读",
        tags=["operation"],
    )
    async def test_mark_all_as_read(api, config):
        """标记全部已读"""
        await api.mark_all_as_read()
        return {"action": "mark_all_as_read", "status": "success"}
