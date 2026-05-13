import dataclasses

import pytest


@dataclasses.dataclass
class FakeTool:
    name: str
    description: str = "A fake tool for testing"


@pytest.fixture()
def fake_tool_factory() -> object:
    def _make(name: str) -> FakeTool:
        return FakeTool(name=name)

    return _make
