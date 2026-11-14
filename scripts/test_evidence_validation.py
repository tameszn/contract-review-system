
from app.agents.liability_agent import analyze_liability
from app.validation.evidence_validator import validate_liability_evidence


contract_id = input("Enter contract ID: ").strip()

analysis = analyze_liability(contract_id)

validated_analysis, rejected_findings = validate_liability_evidence(
    contract_id=contract_id,
    analysis=analysis,
)

print("\nEVIDENCE VALIDATION RESULTS")

print(f"\nOriginal findings: {len(analysis.findings)}")
print(f"Validated findings: {len(validated_analysis.findings)}")
print(f"Rejected findings: {len(rejected_findings)}")

for index, finding in enumerate(validated_analysis.findings, start=1):
    print(f"\nValidated Finding {index}")
    print(f"Risk: {finding.risk_level}")
    print(f"Evidence: {finding.evidence_quote}")
    print(f"Page: {finding.page_number}")
    print(f"Confidence: {finding.confidence}")

for index, rejected in enumerate(rejected_findings, start=1):
    print(f"\nRejected Finding {index}")
    print(f"Finding: {rejected['finding']}")
    print(f"Reason: {rejected['reason']}")
