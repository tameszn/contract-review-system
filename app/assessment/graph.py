
from uuid import uuid4

from langgraph.graph import StateGraph, START, END

from app.assessment.graph_state import AssessmentGraphState
from app.assessment.pipeline import (
    AGENT_CONFIG,
    MAX_AGENT_RETRIES,
    run_agent_with_validation,
)
from app.assessment.consolidator import consolidate_findings
from app.assessment.builder import build_risk_assessment
from app.schemas import AgentCoverage

from app.repo import (
    save_analysis_result,
    start_assessment_run,
    finish_assessment_run,
)

AGENT_KEYS = {
    "liability": "liability",
    "financial": "financial",
    "termination_ip": "termination_ip",
    "compliance": "compliance",
}


def make_agent_node(agent_name):
    def agent_node(state: AssessmentGraphState):
        result = run_agent_with_validation(
            agent_name=agent_name,
            contract_id=state["contract_id"],
            run_id=state["run_id"],
            max_retries=0,
        )
        return {
            f"{agent_name}_analysis": result["analysis"],
            f"{agent_name}_status": result["status"],
            f"{agent_name}_error": result["error"],
            f"{agent_name}_metadata": result["metadata"],
        }
    return agent_node


def quality_gate_node(state: AssessmentGraphState):
    statuses = [
        state.get(f"{name}_status", "failed")
        for name in AGENT_KEYS
    ]
    retry_round = state.get("retry_round", 0)

    if all(status == "completed" for status in statuses):
        decision = "continue"
    elif retry_round < 1:
        decision = "retry"
    else:
        decision = "partial"

    return {"gate_decision": decision}


def route_quality_gate(state: AssessmentGraphState):
    return state["gate_decision"]


def retry_failed_agents_node(state: AssessmentGraphState):
    updates = {}

    for agent_name in AGENT_KEYS:
        status_key = f"{agent_name}_status"

        if state.get(status_key) != "failed":
            continue

        previous_metadata = state.get(f"{agent_name}_metadata", {})

        result = run_agent_with_validation(
            agent_name=agent_name,
            contract_id=state["contract_id"],
            run_id=state["run_id"],
            max_retries=max(0, MAX_AGENT_RETRIES - 1),
        )

        retry_metadata = result["metadata"]
        retry_metadata["attempts"] += previous_metadata.get("attempts", 0)
        retry_metadata["max_attempts"] = MAX_AGENT_RETRIES + 1
        retry_metadata["attempt_errors"] = (
            previous_metadata.get("attempt_errors", [])
            + retry_metadata.get("attempt_errors", [])
        )

        updates.update({
            f"{agent_name}_analysis": result["analysis"],
            f"{agent_name}_status": result["status"],
            f"{agent_name}_error": result["error"],
            f"{agent_name}_metadata": retry_metadata,
        })

    updates["retry_round"] = state.get("retry_round", 0) + 1
    return updates


def finalize_assessment_node(state: AssessmentGraphState):
    analyses = {
        name: state.get(f"{name}_analysis", AGENT_CONFIG[name]["empty"]())
        for name in AGENT_KEYS
    }

    coverage = [
        AgentCoverage(
            agent_name=name,
            status=state.get(f"{name}_status", "failed"),
            finding_count=len(analyses[name].findings),
            error=state.get(f"{name}_error"),
        )
        for name in AGENT_KEYS
    ]

    completed_agents = [
        item.agent_name for item in coverage
        if item.status == "completed"
    ]
    failed_agents = [
        item.agent_name for item in coverage
        if item.status == "failed"
    ]

    if not completed_agents:
        raise RuntimeError(
            "Assessment aborted: all specialist agents failed."
        )

    findings = consolidate_findings(
        liability=analyses["liability"],
        financial=analyses["financial"],
        termination_ip=analyses["termination_ip"],
        compliance=analyses["compliance"],
    )

    assessment = build_risk_assessment(
        findings=findings,
        coverage=coverage,
    )

    if failed_agents:
        assessment.review_items.append(
            "Partial assessment: failed agents after retry: "
            + ", ".join(failed_agents)
            + ". Review agent coverage before relying on this assessment."
        )

    result_id = save_analysis_result(
        contract_id=state["contract_id"],
        analysis_type="risk_assessment",
        result=assessment,
        run_id=state["run_id"],
    )

    agent_metadata = {
        name: state.get(f"{name}_metadata", {})
        for name in AGENT_KEYS
    }

    execution_metadata = {
        "run_id": state["run_id"],
        "gate_decision": state.get("gate_decision"),
        "retry_round": state.get("retry_round", 0),
        "agent_statuses": {
            item.agent_name: item.status for item in coverage
        },
        "completed_agents": completed_agents,
        "failed_agents": failed_agents,
        "agent_metadata": agent_metadata,
        "total_attempts": sum(
            metadata.get("attempts", 0)
            for metadata in agent_metadata.values()
        ),
    }

    return {
        "assessment": assessment,
        "result_id": result_id,
        "execution_metadata": execution_metadata,
    }


def build_assessment_graph():
    graph = StateGraph(AssessmentGraphState)

    for agent_name in AGENT_KEYS:
        graph.add_node(agent_name, make_agent_node(agent_name))

    graph.add_node("quality_gate", quality_gate_node)
    graph.add_node("retry_failed_agents", retry_failed_agents_node)
    graph.add_node("finalize", finalize_assessment_node)

    for agent_name in AGENT_KEYS:
        graph.add_edge(START, agent_name)

    graph.add_edge(list(AGENT_KEYS), "quality_gate")

    graph.add_conditional_edges(
        "quality_gate",
        route_quality_gate,
        {
            "retry": "retry_failed_agents",
            "continue": "finalize",
            "partial": "finalize",
        },
    )

    graph.add_edge("retry_failed_agents", "quality_gate")
    graph.add_edge("finalize", END)

    return graph.compile()



def run_graph_assessment(contract_id: str):
    run_id = str(uuid4())
    start_assessment_run(contract_id, run_id)

    try:
        result = build_assessment_graph().invoke({
            "contract_id": contract_id,
            "run_id": run_id,
            "retry_round": 0,
        })

        metadata = result["execution_metadata"]
        failed_agents = metadata.get("failed_agents", [])
        status = "partial" if failed_agents else "completed"

        finish_assessment_run(
            run_id=run_id,
            status=status,
            execution_metadata=metadata,
            gate_decision=metadata.get("gate_decision"),
        )

        return {
            "assessment": result["assessment"],
            "result_id": result["result_id"],
            "execution_metadata": metadata,
        }

    except Exception as exc:
        finish_assessment_run(
            run_id=run_id,
            status="failed",
            execution_metadata={
                "run_id": run_id,
                "failure": str(exc),
            },
            error=str(exc),
        )
        raise

