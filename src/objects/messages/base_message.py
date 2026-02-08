from pydantic import BaseModel


class BaseMessage(BaseModel):
    request_id: str
    topic_name: str
