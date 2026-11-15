
import re
from uuid import uuid4

from app.schemas import (
    ConsolidatedFinding,
    LiabilityAnalysis,
    FinancialAnalysis,
    TerminationIPAnalysis,
    ComplianceAnalysis,
)


def normalize_text(text: str) -> str:
    """Normalize text for duplicate comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_risk_level(risk_level: str) -> str:
    """
    Normalize agent severity labels into the four supported levels.
    MUST RULE that Only low, medium, high, and critical are supported.
    'moderate' maps to 'medium'.
    'extreme' and 'severe' map to 'critical'.
    

    """
    normalized = risk_level.strip().lower()

    severity_mapping = {
        "low": "low",
        "medium": "medium",
        "moderate": "medium",
        "high": "high",
        "critical": "critical",
        "extreme": "critical",
        "severe": "critical",
    }

    if normalized not in severity_mapping:
        raise ValueError(
            f"Unsupported risk level returned by agent: {risk_level!r}"
        )

    return severity_mapping[normalized]


def are_duplicates(
    first: ConsolidatedFinding,
    second: ConsolidatedFinding,
) -> bool:
    """Check whether two findings describe the same issue and evidence."""

    if first.page_number != second.page_number:
        return False

    quote1 = normalize_text(first.evidence_quote)
    quote2 = normalize_text(second.evidence_quote)

    if not quote1 or not quote2:
        return False

    quote_tokens1 = set(quote1.split())
    quote_tokens2 = set(quote2.split())

    quote_similarity = (
        len(quote_tokens1 & quote_tokens2)
        / len(quote_tokens1 | quote_tokens2)
    )

    finding1 = set(normalize_text(first.finding).split())
    finding2 = set(normalize_text(second.finding).split())

    finding_similarity = (
        len(finding1 & finding2) / len(finding1 | finding2)
        if finding1 and finding2
        else 0
    )

    return quote_similarity >= 0.80 and finding_similarity >= 0.65


def consolidate_findings(
    liability: LiabilityAnalysis,
    financial: FinancialAnalysis,
    termination_ip: TerminationIPAnalysis,
    compliance: ComplianceAnalysis,
) -> list[ConsolidatedFinding]:
    """
    Consolidate evidence-validated findings from specialist agents.

    Duplicate findings are merged while preserving their source agents.
    Severity disagreements are deliberately not resolved here.
    
    Do not use extreme or severe as risk levels. Only low, medium, high, and critical are supported.
    """  

    findings: list[ConsolidatedFinding] = []

    agent_results = [
        ("liability", liability),
        ("financial", financial),
        ("termination_ip", termination_ip),
        ("compliance", compliance),
    ]

    for agent_name, analysis in agent_results:

        for item in analysis.findings:

            if agent_name == "liability":
                category = item.clause_type
                financial_impact = None
                applicable_requirement = None

            elif agent_name == "financial":
                category = item.financial_category
                financial_impact = item.financial_impact
                applicable_requirement = None

            elif agent_name == "termination_ip":
                category = item.issue_category
                financial_impact = None
                applicable_requirement = None

            else:
                category = item.compliance_category
                financial_impact = None
                applicable_requirement = item.applicable_requirement

            candidate = ConsolidatedFinding(
                finding_id=str(uuid4()),
                source_agents=[agent_name],
                category=category,
                risk_level=normalize_risk_level(item.risk_level),
                finding=item.finding,
                evidence_quote=item.evidence_quote,
                page_number=item.page_number,
                rationale=item.rationale,
                recommendation=item.recommendation,
                confidence=item.confidence,
                financial_impact=financial_impact,
                applicable_requirement=applicable_requirement,
            )

            duplicate = next(
                (
                    existing
                    for existing in findings
                    if are_duplicates(existing, candidate)
                ),
                None,
            )

            if duplicate:
                if agent_name not in duplicate.source_agents:
                    duplicate.source_agents.append(agent_name)

            else:
                findings.append(candidate)

    return findings
