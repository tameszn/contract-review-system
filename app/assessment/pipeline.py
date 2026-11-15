
from app.agents.liability_agent import analyze_liability
from app.agents.financial_agent import analyze_financial_terms
from app.agents.termination_ip_agent import analyze_termination_ip
from app.agents.compliance_agent import analyze_compliance

from app.validation.evidence_validator import validate_analysis_evidence

from app.assessment.consolidator import consolidate_findings
from app.assessment.builder import build_risk_assessment

from app.schemas import (
    LiabilityAnalysis,
    FinancialAnalysis,
    TerminationIPAnalysis,
    ComplianceAnalysis,
)

from app.repo import save_analysis_result


AGENT_CONFIG = {
    "liability": {
        "run": analyze_liability,
        "empty_analysis": LiabilityAnalysis,
        "analysis_type": "liability",
    },
    "financial": {
        "run": analyze_financial_terms,
        "empty_analysis": FinancialAnalysis,
        "analysis_type": "financial",
    },
    "termination_ip": {
        "run": analyze_termination_ip,
        "empty_analysis": TerminationIPAnalysis,
        "analysis_type": "termination_ip",
    },
    "compliance": {
        "run": analyze_compliance,
        "empty_analysis": ComplianceAnalysis,
        "analysis_type": "compliance",
    },
}


def run_agent_with_validation(
    contract_id: str,
    agent_name: str,
    config: dict,
) -> tuple:
    """
    Execute one specialist agent and validate its evidence.

    Returns:
        validated_analysis
        agent_status
        error
        execution_metadata
    """

    metadata = {
        "original_count": 0,
        "validated_count": 0,
        "rejected_count": 0,
    }

    try:
        # Execute specialist agent.
        analysis = config["run"](contract_id)

        metadata["original_count"] = len(analysis.findings)

        # Verify every finding against its cited contract page.
        validated_analysis, rejected_findings = (
            validate_analysis_evidence(
                contract_id,
                analysis,
            )
        )

        metadata["validated_count"] = len(
            validated_analysis.findings
        )

        metadata["rejected_count"] = len(rejected_findings)

        return (
            validated_analysis,
            "completed",
            None,
            metadata,
        )

    except Exception as exc:
        # Preserve the rest of the assessment if one agent fails.
        return (
            config["empty_analysis"](
                overall_assessment=(
                    f"{agent_name} analysis was unavailable."
                ),
                findings=[],
            ),
            "failed",
            f"{type(exc).__name__}: {str(exc)}",
            metadata,
        )


def run_unified_assessment(
    contract_id: str,
) -> dict:
    """
    Run the complete unified contract risk assessment.

    Workflow:
        1. Run all specialist agents.
        2. Validate their evidence.
        3. Preserve successful agent results.
        4. Consolidate validated findings.
        5. Calculate risk scores and generate summary.
        6. Build the final RiskAssessment.
        7. Persist the final assessment in Supabase.

    Agent failures do not automatically abort the assessment.
    """

    if not contract_id or not contract_id.strip():
        raise ValueError("A valid contract_id is required.")

    validated_analyses = {}
    coverage = []
    execution_metadata = {}

    # --------------------------------------------------
    # 1. Execute and validate specialist agents.
    # --------------------------------------------------

    for agent_name, config in AGENT_CONFIG.items():

        (
            validated_analysis,
            status,
            error,
            metadata,
        ) = run_agent_with_validation(
            contract_id,
            agent_name,
            config,
        )

        validated_analyses[agent_name] = validated_analysis

        execution_metadata[agent_name] = metadata

        coverage.append(
            {
                "agent_name": agent_name,
                "status": status,
                "finding_count": 0,
                "error": error,
            }
        )

    # --------------------------------------------------
    # 2. Convert coverage dictionaries into Pydantic models.
    # --------------------------------------------------

    from app.schemas import AgentCoverage

    agent_coverage = [
        AgentCoverage.model_validate(item)
        for item in coverage
    ]

    # --------------------------------------------------
    # 3. Consolidate only evidence-validated findings.
    # --------------------------------------------------

    consolidated_findings = consolidate_findings(
        liability=validated_analyses["liability"],
        financial=validated_analyses["financial"],
        termination_ip=validated_analyses["termination_ip"],
        compliance=validated_analyses["compliance"],
    )

    # --------------------------------------------------
    # 4. Build the final assessment.
    # --------------------------------------------------

    assessment = build_risk_assessment(
        findings=consolidated_findings,
        coverage=agent_coverage,
    )
    failed_agents = [
         item.agent_name
         for item in assessment.coverage
         if item.status == "failed"
        ]

    if len(failed_agents) == len(assessment.coverage):
        raise RuntimeError(
            "Unified assessment aborted: all specialist agents failed. "
            "No risk assessment was persisted."
        )

    if failed_agents:
        coverage_warning = (
            " Assessment coverage is incomplete. The following "
            "specialist agents failed: "
            + ", ".join(failed_agents)
            + ". Findings and scores reflect only successfully "
              "completed agents."
        )

        updated_summary = assessment.summary.model_copy(
            update={
                "executive_summary": (
                    assessment.summary.executive_summary
                    + coverage_warning
                )
            }
        )

        assessment = assessment.model_copy(
            update={"summary": updated_summary}
        )
    # --------------------------------------------------
    # 5. Persist the final unified assessment.
    # --------------------------------------------------

    result_id = save_analysis_result(
        contract_id=contract_id,
        analysis_type="risk_assessment",
        result=assessment,
    )

    return {
        "assessment": assessment,
        "result_id": result_id,
        "execution_metadata": execution_metadata,
    }
