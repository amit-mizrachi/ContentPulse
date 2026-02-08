from pydantic import BaseModel

from src.objects.requests.gateway_request import GatewayRequest


class BaseMessage(BaseModel):
    request_id: str
    gateway_request: GatewayRequest
    topic_name: str