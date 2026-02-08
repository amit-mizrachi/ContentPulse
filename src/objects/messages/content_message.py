from src.objects.messages.base_message import BaseMessage
from src.objects.content.raw_content import RawContent


class ContentMessage(BaseMessage):
    topic_name: str = "content-raw"
    raw_content: RawContent
