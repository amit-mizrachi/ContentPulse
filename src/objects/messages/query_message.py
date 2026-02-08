from src.objects.messages.base_message import BaseMessage
from src.objects.requests.query_request import QueryRequest


class QueryMessage(BaseMessage):
    topic_name: str = "query"
    query_request: QueryRequest
