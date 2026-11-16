
import time
from uuid import uuid4
from app.repo import (
    save_analysis_result,
    start_assessment_run,
    finish_assessment_run,
)

from app.agents.liability_agent import analyze_liability
from app.agents.financial_agent import analyze_financial_terms
from app.agents.termination_ip_agent import analyze_termination_ip
from app.agents.compliance_agent import analyze_compliance
from app.schemas import (
    LiabilityAnalysis,
    FinancialAnalysis,
    TerminationIPAnalysis,
    ComplianceAnalysis,
    AgentCoverage,
)
from app.validation.evidence_validator import validate_analysis_evidence
from app.assessment.consolidator import consolidate_findings
from app.assessment.builder import build_risk_assessment
from app.repo import save_analysis_result


MAX_AGENT_RETRIES = 2
RETRY_DELAY_SECONDS = 1


AGENT_CONFIG = {
    "liability": {
        "run": analyze_liability,
        "empty": lambda: LiabilityAnalysis(overall_assessment="Agent failed.", findings=[]),
    },
    "financial": {
        "run": analyze_financial_terms,
        "empty": lambda: FinancialAnalysis(overall_assessment="Agent failed.", findings=[]),
    },
    "termination_ip": {
        "run": analyze_termination_ip,
        "empty": lambda: TerminationIPAnalysis(overall_assessment="Agent failed.", findings=[]),
    },
    "compliance": {
        "run": analyze_compliance,
        "empty": lambda: ComplianceAnalysis(overall_assessment="Agent failed.", findings=[]),
    },
}


def run_agent_with_validation(
    agent_name: str,
    contract_id: str,
    run_id: str | None = None,
    max_retries: int = MAX_AGENT_RETRIES,
):
    if agent_name not in AGENT_CONFIG:
        raise ValueError(f"Unknown agent: {agent_name}")
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")

    config = AGENT_CONFIG[agent_name]
    max_attempts = max_retries + 1
    attempt_errors = []
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            analysis = config["run"](contract_id)
            original_count = len(analysis.findings)
            validated_analysis, rejected_findings = validate_analysis_evidence(
                contract_id, analysis
            )

            return {
                "analysis": validated_analysis,
                "status": "completed",
                "error": None,
                "metadata": {
                    "run_id": run_id,
                    "agent_name": agent_name,
                    "attempts": attempt,
                    "max_attempts": max_attempts,
                    "original_count": original_count,
                    "validated_count": len(validated_analysis.findings),
                    "rejected_count": len(rejected_findings),
                    "rejected_findings": rejected_findings,
                    "attempt_errors": attempt_errors,
                },
            }
        except Exception as exc:
            last_error = str(exc)
            attempt_errors.append({"attempt": attempt, "error": last_error})
            if attempt < max_attempts:
                time.sleep(RETRY_DELAY_SECONDS)

    return {
        "analysis": config["empty"](),
        "status": "failed",
        "error": last_error,
        "metadata": {
            "run_id": run_id,
            "agent_name": agent_name,
            "attempts": max_attempts,
            "max_attempts": max_attempts,
            "original_count": 0,
            "validated_count": 0,
            "rejected_count": 0,
            "rejected_findings": [],
            "attempt_errors": attempt_errors,
        },
    }



def run_unified_assessment(contract_id: str):
    run_id = str(uuid4())
    start_assessment_run(contract_id, run_id)

    analyses, coverage, agent_metadata = {}, [], {}
    execution_metadata = {"run_id": run_id}

    try:
        for agent_name in AGENT_CONFIG:
            result = run_agent_with_validation(
                agent_name=agent_name,
                contract_id=contract_id,
                run_id=run_id,
            )
            analyses[agent_name] = result["analysis"]
            agent_metadata[agent_name] = result["metadata"]
            coverage.append(AgentCoverage(
                agent_name=agent_name,
                status=result["status"],
                finding_count=len(result["analysis"].findings),
                error=result["error"],
            ))

        failed_agents = [x.agent_name for x in coverage if x.status == "failed"]
        completed_agents = [x.agent_name for x in coverage if x.status == "completed"]

        execution_metadata.update({
            "agent_statuses": {x.agent_name: x.status for x in coverage},
            "completed_agents": completed_agents,
            "failed_agents": failed_agents,
            "agent_metadata": agent_metadata,
            "total_attempts": sum(m["attempts"] for m in agent_metadata.values()),
            "total_original_findings": sum(m["original_count"] for m in agent_metadata.values()),
            "total_validated_findings": sum(m["validated_count"] for m in agent_metadata.values()),
            "total_rejected_findings": sum(m["rejected_count"] for m in agent_metadata.values()),
        })

        if not completed_agents:
            raise RuntimeError("All specialist agents failed.")

        findings = consolidate_findings(
            liability=analyses["liability"],
            financial=analyses["financial"],
            termination_ip=analyses["termination_ip"],
            compliance=analyses["compliance"],
        )
        assessment = build_risk_assessment(findings=findings, coverage=coverage)

        if failed_agents:
            assessment.review_items.append(
                "Partial assessment: failed agents after retries: "
                + ", ".join(failed_agents)
                + ". Review agent coverage before relying on this assessment."
            )

        result_id = save_analysis_result(
            contract_id=contract_id,
            analysis_type="risk_assessment",
            result=assessment,
            run_id=run_id,
        )

        execution_metadata["result_id"] = result_id
        run_status = "partial" if failed_agents else "completed"

        finish_assessment_run(
            run_id=run_id,
            status=run_status,
            execution_metadata=execution_metadata,
        )

        return {
            "assessment": assessment,
            "result_id": result_id,
            "execution_metadata": execution_metadata,
        }

    except Exception as exc:
        execution_metadata["failure"] = str(exc)
        finish_assessment_run(
            run_id=run_id,
            status="failed",
            execution_metadata=execution_metadata,
            error=str(exc),
        )
        raise

