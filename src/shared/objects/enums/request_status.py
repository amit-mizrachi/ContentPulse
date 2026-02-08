from enum import Enum


class RequestStatus(str, Enum):
    Accepted = "Accepted"
    Rejected = "Rejected"
