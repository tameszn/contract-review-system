
from app.assessment.builder import build_risk_assessment
from app.schemas import (
    AgentCoverage,
    AssessmentSummary,
    ConsolidatedFinding,
    PriorityRecommendation,
)


def make_finding(
    finding_id,
    category,
    risk_level,
    source_agents,
    requires_review=False,
    review_reason=None,
):
    return ConsolidatedFinding(
        finding_id=finding_id,
        source_agents=source_agents,
        category=category,
        risk_level=risk_level,
        finding=f"Test finding {finding_id}",
        evidence_quote=f"Evidence for {finding_id}",
        page_number=5,
        rationale="Test rationale",
        recommendation=f"Recommendation for {finding_id}",
        confidence=0.90,
        requires_review=requires_review,
        review_reason=review_reason,
    )


def test_assessment_builder():

    findings = [
        make_finding(
            "F001",
            "Liability",
            "high",
            ["liability", "financial"],
            requires_review=True,
            review_reason="The indemnity scope needs legal interpretation.",
        ),
        make_finding(
            "F002",
            "Financial",
            "medium",
            ["financial"],
        ),
        make_finding(
            "F003",
            "Compliance",
            "low",
            ["compliance"],
        ),
    ]

    coverage = [
        AgentCoverage(
            agent_name="liability",
            status="completed",
            finding_count=0,
        ),
        AgentCoverage(
            agent_name="financial",
            status="completed",
            finding_count=0,
        ),
        AgentCoverage(
            agent_name="termination_ip",
            status="failed",
            finding_count=0,
            error="Test failure",
        ),
        AgentCoverage(
            agent_name="compliance",
            status="completed",
            finding_count=0,
        ),
    ]

    summary = AssessmentSummary(
        executive_summary=(
            "The contract contains a significant liability concern "
            "and additional financial and compliance issues."
        ),
        priorities=[
            PriorityRecommendation(
                finding_id="F001",
                priority_rank=1,
                recommendation="Review and negotiate the indemnity scope.",
            ),
            PriorityRecommendation(
                finding_id="F002",
                priority_rank=2,
                recommendation="Clarify payment obligations.",
            ),
        ],
    )

    assessment = build_risk_assessment(
        findings=findings,
        coverage=coverage,
        summary=summary,
    )

    # Overall score: 7 + 3 + 1 = 11.
    assert assessment.overall_score == 11
    assert assessment.overall_risk_level == "medium"

    # Findings must remain ranked by severity.
    assert assessment.ranked_findings[0].finding_id == "F001"

    # Agent contribution counts.
    contribution_map = {
        item.agent_name: item.finding_count
        for item in assessment.coverage
    }

    assert contribution_map["liability"] == 1
    assert contribution_map["financial"] == 2
    assert contribution_map["termination_ip"] == 0
    assert contribution_map["compliance"] == 1

    # Failed agent status must be preserved.
    failed_agent = next(
        item
        for item in assessment.coverage
        if item.agent_name == "termination_ip"
    )

    assert failed_agent.status == "failed"
    assert failed_agent.error == "Test failure"

    # Human review items.
    assert len(assessment.review_items) == 1
    assert "F001" in assessment.review_items[0]
    assert "legal interpretation" in assessment.review_items[0]

    # Summary preservation.
    assert assessment.summary.executive_summary
    assert len(assessment.summary.priorities) == 2

    print("PASSED: overall assessment construction")
    print("PASSED: deterministic risk scoring")
    print("PASSED: agent contribution counts")
    print("PASSED: failed agent coverage")
    print("PASSED: human review items")
    print("PASSED: summary integration")


def test_empty_assessment():

    summary = AssessmentSummary(
        executive_summary="No validated findings were supplied.",
        priorities=[],
    )

    assessment = build_risk_assessment(
        findings=[],
        coverage=[
            AgentCoverage(
                agent_name="liability",
                status="completed",
                finding_count=0,
            ),
            AgentCoverage(
                agent_name="financial",
                status="skipped",
                finding_count=0,
            ),
        ],
        summary=summary,
    )

    assert assessment.overall_score == 0
    assert assessment.overall_risk_level == "low"
    assert assessment.ranked_findings == []
    assert assessment.review_items == []

    print("PASSED: empty assessment")


if __name__ == "__main__":
    test_assessment_builder()
    test_empty_assessment()

    print("\nAll assessment builder tests passed.")
