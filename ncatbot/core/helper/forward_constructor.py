from typing import List, Optional
from ..event import (
    MessageArray,
    Image,
    Text,
    Forward,
    Node,
    File,
    Video,
)


class ForwardConstructor:
    def __init__(
        self,
        user_id: str = "123456",
        nickname: str = "QQ用户",
        content: Optional[List[Node]] = None,
    ):
        self.user_id = user_id
        self.nickname = nickname
        self.content = content if content else []

    def attach(self, content: MessageArray, user_id: Optional[str] = None, nickname: Optional[str] = None):
        self.content.append(
            Node(
                user_id=user_id if user_id else self.user_id,
                nickname=nickname if nickname else self.nickname,
                content=content,
            )
        )

    def attach_text(self, text: str, user_id: Optional[str] = None, nickname: Optional[str] = None):
        self.attach(MessageArray(Text(text)), user_id, nickname)

    def attach_image(self, image: str, user_id: Optional[str] = None, nickname: Optional[str] = None):
        self.attach(MessageArray(Image(file=image)), user_id, nickname)

    def attach_file(self, file: str, user_id: Optional[str] = None, nickname: Optional[str] = None):
        self.attach(MessageArray(File(file=file)), user_id, nickname)

    def attach_video(self, video: str, user_id: Optional[str] = None, nickname: Optional[str] = None):
        self.attach(MessageArray(Video(file=video)), user_id, nickname)

    def attach_forward(
        self, forward: Forward, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        if forward.content is None:
            raise ValueError("Forward 对象的 content 不能为空")
        self.attach(MessageArray(forward), user_id, nickname)

    def attach_message_id(
        self, message_id: str, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        pass

    def to_forward(self) -> Forward:
        return Forward(content=self.content)
