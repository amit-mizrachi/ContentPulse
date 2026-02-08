from src.shared.objects.messages.base_message import BaseMessage
from src.shared.objects.content.raw_article import RawArticle


class ContentMessage(BaseMessage):
    topic_name: str = "content-raw"
    raw_content: RawArticle
