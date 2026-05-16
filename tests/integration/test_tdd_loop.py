"""Integration tests: full orchestrator TDD loop with mocked agent graphs."""

from __future__ import annotations

from dev_team_state import TaskStatus
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from orchestrator.graph import build_orchestrator_graph

from tests.integration.conftest import initial_state


class TestTDDFullLoop:
    async def test_full_tdd_loop_completes(
        self,
        mock_guardrail_pass: None,
        mock_tdd_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-full-001"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert result["status"] == TaskStatus.COMPLETED
        assert len(result["agent_results"]) == 4
        assert result["agent_results"][0]["agent_id"] == "test_agent"
        assert result["agent_results"][1]["agent_id"] == "code_agent"
        assert result["agent_results"][2]["agent_id"] == "code_review_agent"
        assert result["agent_results"][3]["agent_id"] == "git_agent"

    async def test_all_subtasks_marked_completed(
        self,
        mock_guardrail_pass: None,
        mock_tdd_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-full-002"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert all(s["status"] == "completed" for s in result["plan"])

    async def test_test_file_path_propagates_to_code_agent(
        self,
        mock_guardrail_pass: None,
        mock_tdd_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-full-003"}}
        result = await graph.ainvoke(initial_state(), config=config)

        code_result = next(r for r in result["agent_results"] if r["agent_id"] == "code_agent")
        assert code_result["metadata"].get("test_file_path") == "/workspace/tests/test_feature.py"

    async def test_git_agent_pr_url_propagates_to_orchestrator(
        self,
        mock_guardrail_pass: None,
        mock_tdd_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-full-004"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert result["pr_url"] == "https://github.com/org/repo/pull/1"

    async def test_all_subtask_agent_ids_recorded(
        self,
        mock_guardrail_pass: None,
        mock_tdd_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-full-005"}}
        result = await graph.ainvoke(initial_state(), config=config)

        recorded_agents = [r["agent_id"] for r in result["agent_results"]]
        assert "test_agent" in recorded_agents
        assert "code_agent" in recorded_agents
        assert "code_review_agent" in recorded_agents
        assert "git_agent" in recorded_agents


class TestHITLInterrupt:
    async def test_approval_subtask_interrupts_before_git_agent(
        self,
        mock_guardrail_pass: None,
        mock_approval_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-hitl-001"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert "__interrupt__" in result
        interrupt_value = result["__interrupt__"][0].value
        assert interrupt_value["agent_type"] == "git_agent"

    async def test_resume_after_approval_completes(
        self,
        mock_guardrail_pass: None,
        mock_approval_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-hitl-002"}}
        await graph.ainvoke(initial_state(), config=config)

        result = await graph.ainvoke(
            Command(resume={"approved": True, "approved_by": "eng@test.com"}),
            config=config,
        )

        assert result["status"] == TaskStatus.COMPLETED
        assert len(result["human_approvals"]) == 1
        assert result["human_approvals"][0]["approved"] is True
        assert result["human_approvals"][0]["approved_by"] == "eng@test.com"

    async def test_resume_with_rejection_still_runs_agent(
        self,
        mock_guardrail_pass: None,
        mock_approval_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-hitl-003"}}
        await graph.ainvoke(initial_state(), config=config)

        result = await graph.ainvoke(
            Command(resume={"approved": False, "approved_by": "eng@test.com"}),
            config=config,
        )

        assert result["human_approvals"][0]["approved"] is False


class TestGuardrailBlock:
    async def test_unsafe_task_blocked_before_planning(
        self,
        mock_guardrail_fail: None,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-guard-001"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert result["guardrail_passed"] is False
        assert result["plan"] == []
        assert result["agent_results"] == []

    async def test_unsafe_task_status_not_completed(
        self,
        mock_guardrail_fail: None,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-guard-002"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert result["status"] != TaskStatus.COMPLETED


class TestCrossAgentContext:
    async def test_security_result_passed_to_code_review(
        self,
        mock_guardrail_pass: None,
        mock_security_then_review_plan_llm: object,
        mock_context_llm: object,
        mock_all_agent_graphs: None,
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "integ-cross-001"}}
        result = await graph.ainvoke(initial_state(), config=config)

        assert result["status"] == TaskStatus.COMPLETED
        security_result = next(
            r for r in result["agent_results"] if r["agent_id"] == "security_agent"
        )
        assert security_result["metadata"]["scan_complete"] is True
        review_result = next(
            r for r in result["agent_results"] if r["agent_id"] == "code_review_agent"
        )
        assert review_result["status"] == "completed"
