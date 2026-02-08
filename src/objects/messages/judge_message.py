from src.objects.messages.base_message import BaseMessage
from src.objects.results.inference_result import InferenceResult


class JudgeMessage(BaseMessage):
    topic_name: str = "judge"
    inference_result: InferenceResult

    def get_inference_response(self) -> str:
        return self.inference_result.response

    def get_judge_model_identifier(self) -> str:
        return self.gateway_request.get_judge_model_identifier()

    def get_original_prompt(self) -> str:
        return self.gateway_request.prompt
