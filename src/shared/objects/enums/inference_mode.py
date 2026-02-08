"""Inference mode enum."""
from enum import Enum


class InferenceMode(Enum):
    """Whether inference runs against a remote API or a local server."""
    REMOTE = "remote"
    LOCAL = "local"
