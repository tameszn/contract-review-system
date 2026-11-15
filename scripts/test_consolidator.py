from app.schemas import (
    LiabilityAnalysis,
    FinancialAnalysis,
    TerminationIPAnalysis,
    ComplianceAnalysis,
)
from app.assessment.consolidator import consolidate_findings


def main():

    liability = LiabilityAnalysis(
        overall_assessment="Liability risks identified.",
        findings=[
            {
                "clause_type": "Indemnity",
                "risk_level": "high",
                "finding": "Broad indemnification obligation.",
                "evidence_quote": (
                    "The supplier shall indemnify and hold harmless "
                    "the customer against all claims."
                ),
                "page_number": 5,
                "rationale": "The obligation is excessively broad.",
                "recommendation": "Limit indemnification to defined claims.",
                "confidence": 0.92,
            }
        ],
    )

    financial = FinancialAnalysis(
        overall_assessment="Financial risks identified.",
        findings=[
            {
                "financial_category": "Indemnification costs",
                "risk_level": "medium",
                "finding": "Broad indemnification obligation.",
                "evidence_quote": (
                    "The supplier shall indemnify and hold harmless "
                    "the customer against all claims."
                ),
                "page_number": 5,
                "financial_impact": "Potential unlimited financial exposure.",
                "rationale": "The obligation has no apparent financial cap.",
                "recommendation": "Introduce a reasonable liability cap.",
                "confidence": 0.85,
            },
            {
                "financial_category": "Payment terms",
                "risk_level": "high",
                "finding": "Unclear payment deadline.",
                "evidence_quote": "Payment shall be made promptly.",
                "page_number": 8,
                "financial_impact": "Potential payment disputes.",
                "rationale": "No specific payment deadline is provided.",
                "recommendation": "Specify a payment deadline.",
                "confidence": 0.90,
            }
        ],
    )

    termination_ip = TerminationIPAnalysis(
        overall_assessment="No significant termination risks.",
        findings=[],
    )

    compliance = ComplianceAnalysis(
        overall_assessment="No significant compliance risks.",
        findings=[],
    )

    findings = consolidate_findings(
        liability,
        financial,
        termination_ip,
        compliance,
    )

    print(f"\nConsolidated findings: {len(findings)}")

    for item in findings:
        print("\nFinding ID:", item.finding_id)
        print("Category:", item.category)
        print("Source agents:", item.source_agents)
        print("Risk level:", item.risk_level)
        print("Page:", item.page_number)
        print("Evidence:", item.evidence_quote)

    assert len(findings) == 2, "Unexpected consolidation count."

    duplicate = next(
        item for item in findings
        if len(item.source_agents) > 1
    )

    assert set(duplicate.source_agents) == {"liability", "financial"}

    print("\nAll consolidation tests passed.")


if __name__ == "__main__":
    main()