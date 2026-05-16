"""TDD tests for the checkpointer factory — written before implementation (RED phase)."""

from __future__ import annotations

import pytest
from dev_team_state.checkpointer import get_checkpointer
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


requires_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker is not available on this machine",
)


class _MinimalState(TypedDict):
    value: str


def _passthrough(state: _MinimalState) -> _MinimalState:
    return {"value": state["value"] + "_processed"}


_builder: StateGraph = StateGraph(_MinimalState)
_builder.add_node("passthrough", _passthrough)
_builder.add_edge(START, "passthrough")
_builder.add_edge("passthrough", END)


class TestGetCheckpointerFactory:
    async def test_returns_in_memory_saver_when_no_redis_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("REDIS_URL", raising=False)
        async with get_checkpointer() as cp:
            assert isinstance(cp, InMemorySaver)

    async def test_in_memory_saver_is_usable_in_graph(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("REDIS_URL", raising=False)
        async with get_checkpointer() as cp:
            graph = _builder.compile(checkpointer=cp)
            result = await graph.ainvoke(
                {"value": "hello"},
                config={"configurable": {"thread_id": "test-inmem-1"}},
            )
            assert result["value"] == "hello_processed"


@requires_docker
class TestAsyncRedisSaverRoundTrip:
    async def test_asetup_creates_indices(self, redis_saver: AsyncRedisSaver) -> None:
        # asetup() already called in the fixture; verify the index is queryable
        config = {"configurable": {"thread_id": "probe-thread"}}
        result = await redis_saver.aget_tuple(config)
        assert result is None  # thread doesn't exist yet, but the call succeeds (no FT error)

    async def test_write_read_round_trip(self, redis_url: str) -> None:
        async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
            await saver.asetup()
            graph = _builder.compile(checkpointer=saver)
            config = {"configurable": {"thread_id": "test-redis-rw-1"}}
            await graph.ainvoke({"value": "ping"}, config=config)
            checkpoint = await saver.aget_tuple(config)
        assert checkpoint is not None

    async def test_aget_tuple_returns_none_for_unknown_thread(
        self, redis_saver: AsyncRedisSaver
    ) -> None:
        config = {"configurable": {"thread_id": "nonexistent-thread-xyz"}}
        result = await redis_saver.aget_tuple(config)
        assert result is None

    async def test_second_invocation_appends_checkpoint(self, redis_url: str) -> None:
        async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
            await saver.asetup()
            graph = _builder.compile(checkpointer=saver)
            config = {"configurable": {"thread_id": "test-redis-multi-1"}}
            await graph.ainvoke({"value": "first"}, config=config)
            await graph.ainvoke({"value": "second"}, config=config)
            history = [c async for c in saver.alist(config)]
        assert len(history) >= 2
