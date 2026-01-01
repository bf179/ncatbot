"""
群聊消息相关 API 测试用例
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import test_case, APITestSuite


# ============================================================================
# 辅助函数
# ============================================================================

async def send_group_test_message(api, target_group: int) -> str:
    """发送群聊测试消息并返回 message_id"""
    # 使用 post_group_msg 便捷方法
    result = await api.post_group_msg(
        group_id=target_group,
        text="[E2E 测试] 用于转发测试的临时消息",
    )
    # post_group_msg 直接返回 message_id (str)
    return result


def get_message_id(result) -> str:
    """从结果中提取 message_id"""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return str(result.get("message_id", ""))
    if isinstance(result, int):
        return str(result)
    # 尝试从对象属性获取
    msg_id = getattr(result, 'message_id', None)
    if msg_id is not None:
        return str(msg_id)
    return str(result)


def model_to_dict(obj):
    """将模型对象转换为字典"""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in vars(obj).items() if not k.startswith('_')}
    return str(obj)


# ============================================================================
# 测试用例
# ============================================================================

class GroupMessageTests(APITestSuite):
    """群聊消息 API 测试"""

    suite_name = "Group Message API"
    suite_description = "测试群聊消息发送相关 API"

    @staticmethod
    @test_case(
        name="发送群聊文本消息",
        description="向指定群发送纯文本群消息",
        category="message",
        api_endpoint="/send_group_msg",
        expected="返回 message_id，群成员应能看到消息",
        tags=["group", "text"],
        show_result=True,
    )
    async def test_send_group_text(api, data):
        """发送群聊文本消息"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        messages_data = data.get("messages", {})
        content = messages_data.get("text_messages", {}).get("group", {}).get(
            "simple", "[E2E 测试] 群聊文本消息测试"
        )

        result = await api.post_group_msg(
            group_id=int(target_group),
            text=content,
        )
        
        # post_group_msg 直接返回 message_id (str)
        message_id = get_message_id(result)
        assert message_id, "发送消息失败，未获取到 message_id"
        
        return {
            "message_id": message_id,
            "target_group": target_group,
            "content": content,
        }

    @staticmethod
    @test_case(
        name="转发群聊单条消息",
        description="先发送测试消息，然后转发该消息到群聊",
        category="message",
        api_endpoint="/forward_group_single_msg",
        expected="消息转发成功",
        tags=["group", "forward"],
        show_result=True,
    )
    async def test_forward_group_single_msg(api, data):
        """转发群聊单条消息"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 先发送测试消息，send_group_test_message 返回的是 message_id (str)
        message_id = await send_group_test_message(api, int(target_group))
        
        assert message_id, "发送消息失败，未获取到 message_id"

        result = await api.forward_group_single_msg(
            group_id=int(target_group),
            message_id=int(message_id),
        )
        return {
            "target_group": target_group,
            "original_message_id": message_id,
            "result": model_to_dict(result),
        }

    @staticmethod
    @test_case(
        name="发送群音乐分享",
        description="发送 QQ 音乐分享到群聊",
        category="message",
        api_endpoint="/send_group_music",
        expected="音乐分享发送成功",
        tags=["group", "music"],
        show_result=True,
    )
    async def test_send_group_music(api, data):
        """发送群音乐分享"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        messages_data = data.get("messages", {})
        music_info = messages_data.get("music_messages", {}).get("qq_music", {})
        music_type = music_info.get("type", "qq")
        music_id = music_info.get("id", "003aAYrm3GE0Ac")

        result = await api.send_group_music(
            group_id=int(target_group),
            type=music_type,
            id=music_id,
        )
        return {
            "target_group": target_group,
            "music_type": music_type,
            "music_id": music_id,
            "message_id": result,
        }

    @staticmethod
    @test_case(
        name="发送群自定义音乐分享",
        description="发送自定义音乐分享到群聊",
        category="message",
        api_endpoint="/send_group_custom_music",
        expected="自定义音乐分享发送成功",
        tags=["group", "music"],
        show_result=True,
    )
    async def test_send_group_custom_music(api, data):
        """发送群自定义音乐分享"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        messages_data = data.get("messages", {})
        music_info = messages_data.get("music_messages", {}).get("custom_music", {})

        result = await api.send_group_custom_music(
            group_id=int(target_group),
            url=music_info.get("url", "https://music.163.com"),
            audio=music_info.get("audio", "https://music.163.com/song/media/outer/url?id=1.mp3"),
            title=music_info.get("title", "测试音乐"),
            content=music_info.get("content", "测试歌手"),
            image=music_info.get("image", "https://via.placeholder.com/300"),
        )
        return {
            "target_group": target_group,
            "music_title": music_info.get("title", "测试音乐"),
            "message_id": result,
        }

    @staticmethod
    @test_case(
        name="群戳一戳",
        description="在群里戳一戳某人",
        category="message",
        api_endpoint="/group_poke",
        expected="戳一戳成功",
        tags=["group", "poke"],
        show_result=True,
    )
    async def test_group_poke(api, data):
        """群戳一戳"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group or not target_user:
            raise ValueError("需要配置 target_group 和 target_user")

        await api.group_poke(
            group_id=int(target_group),
            user_id=int(target_user),
        )
        return {
            "target_group": target_group,
            "target_user": target_user,
            "action": "group_poke",
        }

    @staticmethod
    @test_case(
        name="发送群数组消息",
        description="使用 MessageArray 发送消息到群聊",
        category="message",
        api_endpoint="/post_group_array_msg",
        expected="消息数组发送成功",
        tags=["group", "array"],
        show_result=True,
    )
    async def test_post_group_array_msg(api, data):
        """发送群数组消息"""
        from ncatbot.core import MessageArray
        
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 使用 MessageArray 构建消息
        msg = MessageArray()
        msg.add_text("[E2E 测试] 数组消息第一段")
        msg.add_text(" | 数组消息第二段")

        result = await api.post_group_array_msg(
            group_id=int(target_group),
            msg=msg,
        )
        return {
            "target_group": target_group,
            "message_id": result,
        }
