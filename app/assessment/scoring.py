from collections import defaultdict

from app.schemas import ConsolidatedFinding, CategoryRiskScore


SEVERITY_WEIGHTS = {
    "low": 1,
    "medium": 3,
    "high": 7,
    "critical": 10,
}

RISK_THRESHOLDS = {
    "low": 5,
    "medium": 15,
}


def get_risk_level(score: int) -> str:
    if score <= RISK_THRESHOLDS["low"]:
        return "low"

    if score <= RISK_THRESHOLDS["medium"]:
        return "medium"

    return "high"


def calculate_risk_scores(
    findings: list[ConsolidatedFinding],
) -> dict:

    overall_score = 0
    category_totals = defaultdict(int)
    category_counts = defaultdict(int)
    category_names = {}

    for finding in findings:
        severity = finding.risk_level.lower()

        if severity not in SEVERITY_WEIGHTS:
            raise ValueError(
                f"Unsupported risk level: {severity}"
            )

        weight = SEVERITY_WEIGHTS[severity]

        overall_score += weight

        category_key = finding.category.strip().casefold()

        category_totals[category_key] += weight
        category_counts[category_key] += 1
        category_names.setdefault(category_key, finding.category.strip())

    category_scores = []

    for category_key, score in category_totals.items():
        category_scores.append(
            CategoryRiskScore(
                category=category_names[category_key],
                score=score,
                finding_count=category_counts[category_key],
                risk_level=get_risk_level(score),
            )
        )

    category_scores.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    ranked_findings = sorted(
        findings,
        key=lambda item: (
            -SEVERITY_WEIGHTS[item.risk_level.lower()],
            -item.confidence,
        ),
    )

    return {
        "overall_score": overall_score,
        "overall_risk_level": get_risk_level(overall_score),
        "category_scores": category_scores,
        "ranked_findings": ranked_findings,
    }