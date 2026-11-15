
from langgraph.graph import StateGraph, START, END

from app.assessment.graph_state import AssessmentGraphState

from app.assessment.pipeline import (
    run_agent_with_validation,
    AGENT_CONFIG,
)

from app.assessment.consolidator import consolidate_findings
from app.assessment.builder import build_risk_assessment

from app.schemas import AgentCoverage
from app.repo import save_analysis_result


# --------------------------------------------------
# 1. Specialist agent nodes
# --------------------------------------------------

def run_liability_node(state: AssessmentGraphState) -> dict:
    analysis, status, error, metadata = run_agent_with_validation(
        state["contract_id"],
        "liability",
        AGENT_CONFIG["liability"],
    )

    return {
        "liability_analysis": analysis,
        "liability_status": status,
        "liability_error": error,
        "liability_metadata": metadata,
    }


def run_financial_node(state: AssessmentGraphState) -> dict:
    analysis, status, error, metadata = run_agent_with_validation(
        state["contract_id"],
        "financial",
        AGENT_CONFIG["financial"],
    )

    return {
        "financial_analysis": analysis,
        "financial_status": status,
        "financial_error": error,
        "financial_metadata": metadata,
    }


def run_termination_ip_node(state: AssessmentGraphState) -> dict:
    analysis, status, error, metadata = run_agent_with_validation(
        state["contract_id"],
        "termination_ip",
        AGENT_CONFIG["termination_ip"],
    )

    return {
        "termination_ip_analysis": analysis,
        "termination_ip_status": status,
        "termination_ip_error": error,
        "termination_ip_metadata": metadata,
    }


def run_compliance_node(state: AssessmentGraphState) -> dict:
    analysis, status, error, metadata = run_agent_with_validation(
        state["contract_id"],
        "compliance",
        AGENT_CONFIG["compliance"],
    )

    return {
        "compliance_analysis": analysis,
        "compliance_status": status,
        "compliance_error": error,
        "compliance_metadata": metadata,
    }


# --------------------------------------------------
# 2. Final assessment node
# --------------------------------------------------

def finalize_assessment_node(
    state: AssessmentGraphState,
) -> dict:

    agent_names = [
        "liability",
        "financial",
        "termination_ip",
        "compliance",
    ]

    coverage = []

    for agent_name in agent_names:
        coverage.append(
            AgentCoverage(
                agent_name=agent_name,
                status=state[f"{agent_name}_status"],
                finding_count=0,
                error=state.get(f"{agent_name}_error"),
            )
        )

    # Stop if every specialist failed.
    if all(item.status == "failed" for item in coverage):
        raise RuntimeError(
            "Unified assessment aborted: all specialist agents failed."
        )

    # Consolidate only validated analyses.
    findings = consolidate_findings(
        liability=state["liability_analysis"],
        financial=state["financial_analysis"],
        termination_ip=state["termination_ip_analysis"],
        compliance=state["compliance_analysis"],
    )

    assessment = build_risk_assessment(
        findings=findings,
        coverage=coverage,
    )

    # Clearly disclose incomplete agent coverage.
    failed_agents = [
        item.agent_name
        for item in assessment.coverage
        if item.status == "failed"
    ]

    if failed_agents:
        warning = (
            " Assessment coverage is incomplete. Failed specialist "
            "agents: "
            + ", ".join(failed_agents)
            + ". Scores and findings reflect only successfully "
              "completed agents."
        )

        updated_summary = assessment.summary.model_copy(
            update={
                "executive_summary": (
                    assessment.summary.executive_summary + warning
                )
            }
        )

        assessment = assessment.model_copy(
            update={"summary": updated_summary}
        )

    # Persist the final assessment.
    result_id = save_analysis_result(
        contract_id=state["contract_id"],
        analysis_type="risk_assessment",
        result=assessment,
    )

    execution_metadata = {
        "liability": state["liability_metadata"],
        "financial": state["financial_metadata"],
        "termination_ip": state["termination_ip_metadata"],
        "compliance": state["compliance_metadata"],
    }

    return {
        "assessment": assessment,
        "result_id": result_id,
        "execution_metadata": execution_metadata,
    }


# --------------------------------------------------
# 3. Construct the graph
# --------------------------------------------------

def build_assessment_graph():
    graph = StateGraph(AssessmentGraphState)

    graph.add_node("liability", run_liability_node)
    graph.add_node("financial", run_financial_node)
    graph.add_node("termination_ip", run_termination_ip_node)
    graph.add_node("compliance", run_compliance_node)
    graph.add_node("finalize", finalize_assessment_node)

    # Fan out: all four specialist agents can execute in parallel.
    graph.add_edge(START, "liability")
    graph.add_edge(START, "financial")
    graph.add_edge(START, "termination_ip")
    graph.add_edge(START, "compliance")

    # Fan in: finalize only after all four branches finish.
    graph.add_edge("liability", "finalize")
    graph.add_edge("financial", "finalize")
    graph.add_edge("termination_ip", "finalize")
    graph.add_edge("compliance", "finalize")

    graph.add_edge("finalize", END)

    return graph.compile()


# --------------------------------------------------
# 4. Public execution function
# --------------------------------------------------

assessment_graph = build_assessment_graph()


def run_graph_assessment(contract_id: str) -> dict:
    if not contract_id or not contract_id.strip():
        raise ValueError("A valid contract_id is required.")

    initial_state: AssessmentGraphState = {
        "contract_id": contract_id,
    }

    result = assessment_graph.invoke(initial_state)

    return {
        "assessment": result["assessment"],
        "result_id": result["result_id"],
        "execution_metadata": result["execution_metadata"],
    }
