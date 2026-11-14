
from app.agents.liability_agent import analyze_liability

contract_id = input("Enter contract ID: ").strip()

result = analyze_liability(contract_id)

print("\nOVERALL ASSESSMENT")
print(result.overall_assessment)

print("\nLIABILITY FINDINGS")

for index, finding in enumerate(result.findings, start=1):
    print(f"\nFinding {index}")
    print(f"Type: {finding.clause_type}")
    print(f"Risk: {finding.risk_level}")
    print(f"Finding: {finding.finding}")
    print(f"Evidence: {finding.evidence_quote}")
    print(f"Page: {finding.page_number}")
    print(f"Rationale: {finding.rationale}")
    print(f"Recommendation: {finding.recommendation}")
    print(f"Confidence: {finding.confidence}")
