from enum import Enum


class RequestStage(str, Enum):
    Gateway = "Gateway"
    QueryProcessing = "QueryProcessing"
    Completed = "Completed"
    Failed = "Failed"
