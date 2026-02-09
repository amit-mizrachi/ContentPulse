from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from typing import Callable


class ContextPreservingThreadPool(ThreadPoolExecutor):
    """
    A ThreadPoolExecutor that preserves context variables (including OTLP telemetry context)
    across thread boundaries. This prevents telemetry context from leaking between threads.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def submit(self, handle_method: Callable, *args, **kwargs):
        context = copy_context()
        return super().submit(context.run, handle_method, *args, **kwargs)
