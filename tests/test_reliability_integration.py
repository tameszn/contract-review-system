
from types import SimpleNamespace

import pytest

from app.assessment import pipeline
from app.assessment import graph as assessment_graph


@pytest.fixture
def fake_assessment():
    return SimpleNamespace(review_items=[])


@pytest.fixture
def mock_run_log(monkeypatch):
    calls = {"started": [], "finished": []}

    monkeypatch.setattr(
        pipeline, "start_assessment_run",
        lambda contract_id, run_id: calls["started"].append(
            (contract_id, run_id)
        ),
    )
    monkeypatch.setattr(
        pipeline, "finish_assessment_run",
        lambda **kwargs: calls["finished"].append(kwargs),
    )
    return calls


def test_sequential_pipeline_completes_with_shared_run_id(
    monkeypatch, fake_assessment, mock_run_log
):
    run_ids = []

    def fake_agent(agent_name, contract_id, run_id=None, **kwargs):
        run_ids.append(run_id)
        analysis = pipeline.AGENT_CONFIG[agent_name]["empty"]()
        return {
            "analysis": analysis,
            "status": "completed",
            "error": None,
            "metadata": {
                "run_id": run_id,
                "attempts": 1,
                "original_count": 0,
                "validated_count": 0,
                "rejected_count": 0,
                "attempt_errors": [],
            },
        }

    monkeypatch.setattr(pipeline, "run_agent_with_validation", fake_agent)
    monkeypatch.setattr(
        pipeline, "consolidate_findings", lambda **kwargs: []
    )
    monkeypatch.setattr(
        pipeline, "build_risk_assessment",
        lambda **kwargs: fake_assessment,
    )
    monkeypatch.setattr(
        pipeline, "save_analysis_result",
        lambda **kwargs: "result-123",
    )

    result = pipeline.run_unified_assessment("contract-123")

    assert result["result_id"] == "result-123"
    assert len(set(run_ids)) == 1
    assert len(run_ids) == 4
    assert mock_run_log["started"][0][1] == run_ids[0]
    assert mock_run_log["finished"][0]["status"] == "completed"


def test_sequential_pipeline_records_partial_completion(
    monkeypatch, fake_assessment, mock_run_log
):
    def fake_agent(agent_name, contract_id, run_id=None, **kwargs):
        failed = agent_name == "financial"
        return {
            "analysis": pipeline.AGENT_CONFIG[agent_name]["empty"](),
            "status": "failed" if failed else "completed",
            "error": "Agent failed" if failed else None,
            "metadata": {
                "run_id": run_id,
                "attempts": 3 if failed else 1,
                "original_count": 0,
                "validated_count": 0,
                "rejected_count": 0,
                "attempt_errors": [],
            },
        }

    monkeypatch.setattr(pipeline, "run_agent_with_validation", fake_agent)
    monkeypatch.setattr(
        pipeline, "consolidate_findings", lambda **kwargs: []
    )
    monkeypatch.setattr(
        pipeline, "build_risk_assessment",
        lambda **kwargs: fake_assessment,
    )
    monkeypatch.setattr(
        pipeline, "save_analysis_result",
        lambda **kwargs: "result-123",
    )

    result = pipeline.run_unified_assessment("contract-123")

    assert "financial" in result["execution_metadata"]["failed_agents"]
    assert result["execution_metadata"]["total_attempts"] == 6
    assert fake_assessment.review_items
    assert mock_run_log["finished"][0]["status"] == "partial"


def test_sequential_pipeline_logs_total_failure(
    monkeypatch, mock_run_log
):
    def fake_agent(agent_name, contract_id, run_id=None, **kwargs):
        return {
            "analysis": pipeline.AGENT_CONFIG[agent_name]["empty"](),
            "status": "failed",
            "error": "Agent failed",
            "metadata": {
                "run_id": run_id,
                "attempts": 3,
                "original_count": 0,
                "validated_count": 0,
                "rejected_count": 0,
                "attempt_errors": [],
            },
        }

    monkeypatch.setattr(pipeline, "run_agent_with_validation", fake_agent)

    with pytest.raises(RuntimeError, match="All specialist agents failed"):
        pipeline.run_unified_assessment("contract-123")

    assert mock_run_log["finished"][0]["status"] == "failed"


def test_graph_retries_only_failed_agents(monkeypatch):
    calls = []

    def fake_runner(agent_name, contract_id, run_id, max_retries):
        calls.append((agent_name, run_id, max_retries))
        return {
            "analysis": assessment_graph.AGENT_CONFIG[agent_name]["empty"](),
            "status": "completed",
            "error": None,
            "metadata": {
                "run_id": run_id,
                "attempts": 1,
                "attempt_errors": [],
            },
        }

    monkeypatch.setattr(
        assessment_graph, "run_agent_with_validation", fake_runner
    )

    state = {
        "contract_id": "contract-123",
        "run_id": "run-123",
        "retry_round": 0,
        "liability_status": "completed",
        "financial_status": "failed",
        "termination_ip_status": "completed",
        "compliance_status": "failed",
        "financial_metadata": {"attempts": 1, "attempt_errors": []},
        "compliance_metadata": {"attempts": 1, "attempt_errors": []},
    }

    result = assessment_graph.retry_failed_agents_node(state)

    assert len(calls) == 2
    assert {call[0] for call in calls} == {"financial", "compliance"}
    assert all(call[1] == "run-123" for call in calls)
    assert all(call[2] == 1 for call in calls)
    assert result["retry_round"] == 1
    assert result["financial_status"] == "completed"
    assert result["compliance_status"] == "completed"


def test_graph_run_logs_completed_execution(monkeypatch):
    calls = {"started": [], "finished": []}

    monkeypatch.setattr(
        assessment_graph, "start_assessment_run",
        lambda contract_id, run_id: calls["started"].append(
            (contract_id, run_id)
        ),
    )
    monkeypatch.setattr(
        assessment_graph, "finish_assessment_run",
        lambda **kwargs: calls["finished"].append(kwargs),
    )

    fake_result = {
        "assessment": "assessment-object",
        "result_id": "result-123",
        "execution_metadata": {
            "run_id": "run-123",
            "failed_agents": [],
            "gate_decision": "continue",
        },
    }

    class FakeGraph:
        def invoke(self, state):
            assert state["run_id"] == calls["started"][0][1]
            return fake_result

    monkeypatch.setattr(
        assessment_graph, "build_assessment_graph",
        lambda: FakeGraph(),
    )
    monkeypatch.setattr(
        assessment_graph, "uuid4",
        lambda: "run-123",
    )

    result = assessment_graph.run_graph_assessment("contract-123")

    assert result["result_id"] == "result-123"
    assert calls["finished"][0]["status"] == "completed"
    assert calls["finished"][0]["gate_decision"] == "continue"


def test_graph_run_logs_partial_execution(monkeypatch):
    calls = {"finished": []}

    monkeypatch.setattr(
        assessment_graph, "start_assessment_run",
        lambda *args: None,
    )
    monkeypatch.setattr(
        assessment_graph, "finish_assessment_run",
        lambda **kwargs: calls["finished"].append(kwargs),
    )

    class FakeGraph:
        def invoke(self, state):
            return {
                "assessment": "assessment-object",
                "result_id": "result-123",
                "execution_metadata": {
                    "run_id": state["run_id"],
                    "failed_agents": ["financial"],
                    "gate_decision": "partial",
                },
            }

    monkeypatch.setattr(
        assessment_graph, "build_assessment_graph",
        lambda: FakeGraph(),
    )

    assessment_graph.run_graph_assessment("contract-123")

    assert calls["finished"][0]["status"] == "partial"
    assert calls["finished"][0]["gate_decision"] == "partial"


def test_graph_run_logs_execution_failure(monkeypatch):
    calls = {"finished": []}

    monkeypatch.setattr(
        assessment_graph, "start_assessment_run",
        lambda *args: None,
    )
    monkeypatch.setattr(
        assessment_graph, "finish_assessment_run",
        lambda **kwargs: calls["finished"].append(kwargs),
    )

    class FakeGraph:
        def invoke(self, state):
            raise RuntimeError("Graph execution failed")

    monkeypatch.setattr(
        assessment_graph, "build_assessment_graph",
        lambda: FakeGraph(),
    )

    with pytest.raises(RuntimeError, match="Graph execution failed"):
        assessment_graph.run_graph_assessment("contract-123")

    assert calls["finished"][0]["status"] == "failed"
    assert "Graph execution failed" in calls["finished"][0]["error"]
