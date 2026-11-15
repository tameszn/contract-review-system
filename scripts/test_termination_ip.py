from app.agents.termination_ip_agent import analyze_termination_ip
from app.validation.evidence_validator import validate_analysis_evidence

contract_id = input("Enter contract ID: ").strip()

analysis=analyze_termination_ip(contract_id)

validated_analysis, rejected_findings = validate_analysis_evidence(
    contract_id=contract_id,
    analysis=analysis
    )

print("\nanalysing")
print(analysis.overall_assessment)

print("\nRESULTS")
print(f"Original findings: {len(analysis.findings)}")
print(f"Validated findings: {len(validated_analysis.findings)}")
print(f"Rejected findings: {len(rejected_findings)}")

for index, finding in enumerate(validated_analysis.findings, start=1):
    print(f"\nFinding {index}")
    print(f"Category: {finding.issue_category}")
    print(f"Risk: {finding.risk_level}")
    print(f"Finding: {finding.finding}")
    print(f"Evidence: {finding.evidence_quote}")
    print(f"Page: {finding.page_number}")
    print(f"Rationale: {finding.rationale}")
    print(f"Recommendation: {finding.recommendation}")
    print(f"Confidence: {finding.confidence}")

print("\nREJECTED FINDINGS")

for finding in rejected_findings:
    print(finding)