from src.objects.messages.base_message import BaseMessage


class InferenceMessage(BaseMessage):
    topic_name: str = "inference"