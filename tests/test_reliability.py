
import pytest

from app.schemas import LiabilityAnalysis
from app.assessment import pipeline
from app.assessment.graph import quality_gate_node, route_quality_gate


@pytest.fixture
def empty_analysis():
    return LiabilityAnalysis(
        overall_assessment="No findings for test.",
        findings=[],
    )


def test_agent_completes_successfully(monkeypatch, empty_analysis):
    monkeypatch.setitem(
        pipeline.AGENT_CONFIG["liability"],
        "run",
        lambda contract_id: empty_analysis,
    )
    monkeypatch.setattr(
        pipeline,
        "validate_analysis_evidence",
        lambda contract_id, analysis: (analysis, []),
    )

    result = pipeline.run_agent_with_validation(
        "liability", "contract-123", run_id="run-123"
    )

    assert result["status"] == "completed"
    assert result["error"] is None
    assert result["metadata"]["attempts"] == 1
    assert result["metadata"]["validated_count"] == 0


def test_agent_retries_after_failure(monkeypatch, empty_analysis):
    calls = {"count": 0}

    def fake_agent(contract_id):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("Temporary failure")
        return empty_analysis

    monkeypatch.setitem(
        pipeline.AGENT_CONFIG["liability"], "run", fake_agent
    )
    monkeypatch.setattr(
        pipeline,
        "validate_analysis_evidence",
        lambda contract_id, analysis: (analysis, []),
    )
    monkeypatch.setattr(pipeline.time, "sleep", lambda _: None)

    result = pipeline.run_agent_with_validation(
        "liability", "contract-123"
    )

    assert result["status"] == "completed"
    assert result["metadata"]["attempts"] == 2
    assert len(result["metadata"]["attempt_errors"]) == 1


def test_agent_fails_after_retry_limit(monkeypatch):
    calls = {"count": 0}

    def failing_agent(contract_id):
        calls["count"] += 1
        raise RuntimeError("Persistent failure")

    monkeypatch.setitem(
        pipeline.AGENT_CONFIG["liability"], "run", failing_agent
    )
    monkeypatch.setattr(pipeline.time, "sleep", lambda _: None)

    result = pipeline.run_agent_with_validation(
        "liability", "contract-123"
    )

    assert result["status"] == "failed"
    assert calls["count"] == pipeline.MAX_AGENT_RETRIES + 1
    assert result["metadata"]["attempts"] == 3
    assert result["error"] == "Persistent failure"


def test_unknown_agent_is_rejected():
    with pytest.raises(ValueError):
        pipeline.run_agent_with_validation(
            "unknown", "contract-123"
        )


def test_negative_retry_limit_is_rejected():
    with pytest.raises(ValueError):
        pipeline.run_agent_with_validation(
            "liability", "contract-123", max_retries=-1
        )


def test_gate_continues_when_all_agents_complete():
    state = {
        "liability_status": "completed",
        "financial_status": "completed",
        "termination_ip_status": "completed",
        "compliance_status": "completed",
        "retry_round": 0,
    }

    result = quality_gate_node(state)

    assert result["gate_decision"] == "continue"


def test_gate_retries_when_an_agent_fails_initially():
    state = {
        "liability_status": "completed",
        "financial_status": "failed",
        "termination_ip_status": "completed",
        "compliance_status": "completed",
        "retry_round": 0,
    }

    result = quality_gate_node(state)

    assert result["gate_decision"] == "retry"


def test_gate_returns_partial_after_retry():
    state = {
        "liability_status": "completed",
        "financial_status": "failed",
        "termination_ip_status": "completed",
        "compliance_status": "completed",
        "retry_round": 1,
    }

    result = quality_gate_node(state)

    assert result["gate_decision"] == "partial"


@pytest.mark.parametrize(
    "decision",
    ["retry", "continue", "partial"],
)
def test_gate_router_routes_all_decisions(decision):
    assert route_quality_gate({"gate_decision": decision}) == decision
