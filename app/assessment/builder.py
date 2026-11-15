
from app.schemas import (
    AgentCoverage,
    AssessmentSummary,
    ConsolidatedFinding,
    RiskAssessment,
)

from app.assessment.scoring import calculate_risk_scores
from app.assessment.summary_chain import generate_assessment_summary


def calculate_agent_contributions(
    findings: list[ConsolidatedFinding],
    coverage: list[AgentCoverage],
) -> list[AgentCoverage]:
    """
    Calculate how many final consolidated findings each agent contributed to.

    A deduplicated finding counts once for each agent in its source_agents.
    Failed and skipped agents retain their execution status.
    """

    contributions = {
        item.agent_name: 0
        for item in coverage
    }

    for finding in findings:
        for agent_name in finding.source_agents:
            if agent_name in contributions:
                contributions[agent_name] += 1

    return [
        item.model_copy(
            update={
                "finding_count": contributions[item.agent_name]
            }
        )
        for item in coverage
    ]


def build_review_items(
    findings: list[ConsolidatedFinding],
) -> list[str]:
    """
    Build human-review items from findings explicitly marked
    as requiring human attention.
    """

    review_items = []

    for finding in findings:
        if not finding.requires_review:
            continue

        reason = (
            finding.review_reason.strip()
            if finding.review_reason
            else "This finding requires human review."
        )

        review_items.append(
            f"{finding.finding_id} — {finding.finding}: {reason}"
        )

    return review_items


def build_risk_assessment(
    findings: list[ConsolidatedFinding],
    coverage: list[AgentCoverage],
    summary: AssessmentSummary | None = None,
) -> RiskAssessment:
    """
    Build the final unified risk assessment.

    If summary is not supplied, the LCEL summary chain generates it.
    Scores and risk levels are always calculated deterministically.
    """

    if len({item.agent_name for item in coverage}) != len(coverage):
        raise ValueError(
            "Agent coverage contains duplicate agent names."
        )

    known_agents = {
        item.agent_name
        for item in coverage
    }

    for finding in findings:
        if not finding.source_agents:
            raise ValueError(
                f"Finding {finding.finding_id} has no source agents."
            )

        unknown_agents = (
            set(finding.source_agents) - known_agents
        )

        if unknown_agents:
            raise ValueError(
                f"Finding {finding.finding_id} references agents "
                f"missing from coverage: {sorted(unknown_agents)}"
            )

    # Deterministic scoring; the LLM does not influence these values.
    scoring_result = calculate_risk_scores(findings)

    # Generate the summary only when one has not already been supplied.
    if summary is None:
        summary = generate_assessment_summary(findings)

    # Count each consolidated finding once per contributing agent.
    final_coverage = calculate_agent_contributions(
        findings,
        coverage,
    )

    review_items = build_review_items(findings)

    assessment = RiskAssessment(
        overall_risk_level=scoring_result["overall_risk_level"],
        overall_score=scoring_result["overall_score"],
        category_scores=scoring_result["category_scores"],
        ranked_findings=scoring_result["ranked_findings"],
        summary=summary,
        review_items=review_items,
        coverage=final_coverage,
    )

    return assessment
