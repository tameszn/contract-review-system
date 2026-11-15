
from app.assessment.summary_chain import generate_assessment_summary
from app.schemas import ConsolidatedFinding


def make_finding(
    finding_id: str,
    category: str,
    risk_level: str,
    finding_text: str,
    quote: str,
    page: int,
    recommendation: str,
) -> ConsolidatedFinding:

    return ConsolidatedFinding(
        finding_id=finding_id,
        source_agents=["liability"],
        category=category,
        risk_level=risk_level,
        finding=finding_text,
        evidence_quote=quote,
        page_number=page,
        rationale="Test rationale supported by the supplied clause.",
        recommendation=recommendation,
        confidence=0.90,
    )


def test_empty_findings():

    result = generate_assessment_summary([])

    assert result.executive_summary
    assert result.priorities == []

    print("PASSED: empty findings")


def test_summary_generation():

    findings = [
        make_finding(
            finding_id="F001",
            category="Liability",
            risk_level="high",
            finding_text=(
                "The supplier has a broad indemnification obligation "
                "without clearly stated limitations."
            ),
            quote=(
                "The supplier shall indemnify and hold harmless "
                "the customer against all claims."
            ),
            page=5,
            recommendation=(
                "Review the scope of indemnification and negotiate "
                "appropriate limitations."
            ),
        ),
        make_finding(
            finding_id="F002",
            category="Payment terms",
            risk_level="medium",
            finding_text=(
                "The payment deadline is not clearly specified."
            ),
            quote="Payment shall be made promptly.",
            page=8,
            recommendation=(
                "Specify a definite payment deadline and payment terms."
            ),
        ),
    ]

    result = generate_assessment_summary(findings)

    assert result.executive_summary.strip()

    valid_ids = {
        finding.finding_id for finding in findings
    }

    for priority in result.priorities:
        assert priority.finding_id in valid_ids
        assert priority.recommendation.strip()

    ranks = [
        priority.priority_rank
        for priority in result.priorities
    ]

    assert sorted(ranks) == list(range(1, len(ranks) + 1))

    print("\nExecutive summary:")
    print(result.executive_summary)

    print("\nPriorities:")

    for priority in result.priorities:
        print(
            f"{priority.priority_rank}. "
            f"{priority.finding_id}: "
            f"{priority.recommendation}"
        )

    print("\nPASSED: summary generation")


if __name__ == "__main__":
    test_empty_findings()
    test_summary_generation()

    print("\nAll summary tests passed.")
