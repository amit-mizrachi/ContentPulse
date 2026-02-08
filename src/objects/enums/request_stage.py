from enum import Enum


class RequestStage(str, Enum):
    Gateway = "Gateway"
    Inference = "Inference"
    Judge = "Judge"
    Completed = "Completed"
    Failed = "Failed"
