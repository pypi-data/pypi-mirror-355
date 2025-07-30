import asyncio
import atexit
import os
from typing import List, Optional, Tuple

from .config import LokiLoggerOptions
from .flush_manager import AsyncFlushManager
from .interceptors import intercept_exceptions, intercept_logging, intercept_print
from .post import post_to_loki
from .safe_flush import safe_flush
from .utils import now_ns, safe_json


class LokiLogger:
    def __init__(self, options: LokiLoggerOptions):
        self.options = options
        self.log_buffer: list[tuple[str, str]] = []
        self.flush_manager = AsyncFlushManager(self)
        intercept_print(self)
        intercept_logging(self)
        intercept_exceptions(self)
        if os.getenv("RUN_MAIN") == "true" or not os.getenv("RUN_MAIN"):
            atexit.register(lambda: safe_flush(self))

    def track_event(self, event_name: str, properties: Optional[dict] = None) -> None:
        ts = now_ns()
        message = (
            f"[EVENT] {event_name} {safe_json(properties)}"
            if properties
            else f"[EVENT] {event_name}"
        )
        self.log_buffer.append((ts, message))
        self.flush_manager.check_and_flush()

    async def flush_logs(self) -> None:
        if not self.log_buffer:
            return
        buffer_copy = self.log_buffer.copy()
        self.log_buffer.clear()
        await self.send_logs(buffer_copy)

    async def send_logs(self, logs: List[Tuple[str, str]]) -> None:
        await post_to_loki(logs, self.options)

    def flush_sync(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.flush_logs(), loop)
            future.result()
        else:
            asyncio.run(self.flush_logs())
