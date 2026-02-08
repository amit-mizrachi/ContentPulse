from pydantic import BaseModel, SecretStr, field_serializer

from src.objects.judge_models.judge_model import JudgeModel
from src.objects.target_models.target_model import TargetModel


class GatewayRequest(BaseModel):
    prompt: str
    target_model: TargetModel
    api_key: SecretStr
    judge_model: JudgeModel

    @field_serializer('api_key', when_used='json')
    def serialize_api_key(self, api_key: SecretStr) -> str:
        return api_key.get_secret_value()

    def get_judge_model_identifier(self) -> str:
        return f"{self.judge_model.name}:{self.judge_model.version}"

    def get_target_model_name(self) -> str:
        return self.target_model.name
    