from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver


@asynccontextmanager
async def get_checkpointer() -> AsyncIterator[BaseCheckpointSaver[Any]]:
    """Yield a checkpointer backed by Redis if REDIS_URL is set, otherwise InMemorySaver."""
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
            await saver.asetup()
            yield saver
    else:
        yield InMemorySaver()
