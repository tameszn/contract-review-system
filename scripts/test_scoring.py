
from app.schemas import ConsolidatedFinding
from app.assessment.scoring import (
    calculate_risk_scores,
    get_risk_level,
    SEVERITY_WEIGHTS,
)


def make_finding(
    finding_id: str,
    category: str,
    risk_level: str,
    confidence: float = 0.9,
) -> ConsolidatedFinding:
    return ConsolidatedFinding(
        finding_id=finding_id,
        source_agents=["liability"],
        category=category,
        risk_level=risk_level,
        finding=f"Test finding {finding_id}",
        evidence_quote=f"Evidence for {finding_id}",
        page_number=1,
        rationale="Testing risk scoring.",
        recommendation="Review this provision.",
        confidence=confidence,
    )


def test_severity_weights():
    assert SEVERITY_WEIGHTS == {
        "low": 1,
        "medium": 3,
        "high": 7,
        "critical": 10,
    }


def test_risk_level_mapping():
    assert get_risk_level(0) == "low"
    assert get_risk_level(5) == "low"
    assert get_risk_level(6) == "medium"
    assert get_risk_level(15) == "medium"
    assert get_risk_level(16) == "high"


def test_empty_findings():
    result = calculate_risk_scores([])

    assert result["overall_score"] == 0
    assert result["overall_risk_level"] == "low"
    assert result["category_scores"] == []
    assert result["ranked_findings"] == []


def test_score_calculation():
    findings = [
        make_finding("F001", "Liability", "high"),
        make_finding("F002", "Financial", "high"),
        make_finding("F003", "Financial", "medium"),
        make_finding("F004", "Compliance", "low"),
    ]

    result = calculate_risk_scores(findings)

    assert result["overall_score"] == 18
    assert result["overall_risk_level"] == "high"

    category_scores = {
        item.category: item
        for item in result["category_scores"]
    }

    assert category_scores["Liability"].score == 7
    assert category_scores["Financial"].score == 10
    assert category_scores["Compliance"].score == 1

    assert category_scores["Financial"].finding_count == 2


def test_finding_ranking():
    findings = [
        make_finding("F001", "Liability", "medium", 0.99),
        make_finding("F002", "Financial", "critical", 0.80),
        make_finding("F003", "Compliance", "high", 0.95),
        make_finding("F004", "Termination", "high", 0.70),
    ]

    result = calculate_risk_scores(findings)

    ranked_ids = [
        item.finding_id
        for item in result["ranked_findings"]
    ]

    assert ranked_ids == [
        "F002", "F003", "F004", "F001"
    ]


def test_invalid_severity():
    from pydantic import ValidationError

    # Test 1: Pydantic should reject unsupported severity labels.
    try:
        make_finding("F001", "Liability", "extreme")
    except ValidationError:
        pass
    else:
        raise AssertionError(
            "Pydantic should reject unsupported severity labels."
        )

    # Test 2: Scoring should also reject invalid data
    # if it somehow bypasses Pydantic validation.
    finding = make_finding("F002", "Liability", "high")

    invalid_finding = ConsolidatedFinding.model_construct(
        **{
            **finding.model_dump(),
            "risk_level": "extreme",
        }
    )

    try:
        calculate_risk_scores([invalid_finding])
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Scoring should reject unsupported severity labels."
        )


def main():
    tests = [
        test_severity_weights,
        test_risk_level_mapping,
        test_empty_findings,
        test_score_calculation,
        test_finding_ranking,
        test_invalid_severity,
    ]

    for test in tests:
        test()
        print(f"PASSED: {test.__name__}")

    print("\nAll scoring tests passed.")


if __name__ == "__main__":
    main()
