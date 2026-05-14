"""Tests for the reviewer node."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from code_review_agent.nodes.reviewer import reviewer
from code_review_agent.schema import CodeReviewAgentState
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AIMessage


class TestReviewerGate:
    async def test_returns_empty_dict_when_scan_not_complete(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        result = await reviewer(minimal_review_state)
        assert result == {}

    async def test_activates_when_scan_complete(
        self,
        mock_deep_agent_reviewer: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        result = await reviewer(scan_complete_state)
        assert "review_result" in result


class TestReviewerOutput:
    async def test_review_result_has_approved_field(
        self,
        mock_deep_agent_reviewer: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        result = await reviewer(scan_complete_state)
        assert "approved" in result["review_result"]  # type: ignore[operator]

    async def test_approved_sets_status_completed(
        self,
        mock_deep_agent_reviewer: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        result = await reviewer(scan_complete_state)
        assert result["status"] == "completed"

    async def test_not_approved_sets_status_awaiting_approval(
        self,
        monkeypatch: pytest.MonkeyPatch,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        rejected_json = (
            '{"approved": false, "reviewer_model": "qwen3.5-72b",'
            ' "comments": [], "blocking_issues": ["Needs tests"], "metadata": {}}'
        )
        mock_client = MagicMock()
        mock_client.get_tools = AsyncMock(return_value=[])
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.MCPRegistry.build_client",
            MagicMock(return_value=mock_client),
        )
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content=rejected_json)]}
        )
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.create_deep_agent",
            MagicMock(return_value=mock_graph),
        )
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.init_chat_model",
            MagicMock(return_value=MagicMock()),
        )
        result = await reviewer(scan_complete_state)
        assert result["status"] == "awaiting_approval"

    async def test_malformed_json_sets_status_failed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_tools = AsyncMock(return_value=[])
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.MCPRegistry.build_client",
            MagicMock(return_value=mock_client),
        )
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="not valid json {{")]}
        )
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.create_deep_agent",
            MagicMock(return_value=mock_graph),
        )
        monkeypatch.setattr(
            "code_review_agent.nodes.reviewer.init_chat_model",
            MagicMock(return_value=MagicMock()),
        )
        result = await reviewer(scan_complete_state)
        assert result["status"] == "failed"


class TestReviewerDeepAgentConfig:
    async def test_passes_github_tools(
        self,
        mock_deep_agent_reviewer: MagicMock,
        mock_github_mcp: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        await reviewer(scan_complete_state)
        call_kwargs = mock_deep_agent_reviewer.call_args.kwargs
        assert len(call_kwargs["tools"]) > 0

    async def test_summarization_middleware_in_stack(
        self,
        mock_deep_agent_reviewer: MagicMock,
        mock_github_mcp: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        await reviewer(scan_complete_state)
        call_kwargs = mock_deep_agent_reviewer.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_configured(
        self,
        mock_deep_agent_reviewer: MagicMock,
        mock_github_mcp: MagicMock,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        await reviewer(scan_complete_state)
        call_kwargs = mock_deep_agent_reviewer.call_args.kwargs
        skills = call_kwargs["skills"]
        assert skills is not None
        assert len(skills) > 0
