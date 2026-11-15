from app.analysis_pipeline import run_compliance_analysis




contract_id = input("Enter contract ID: ").strip()

result = run_compliance_analysis(contract_id)

print("\nCOMPLIANCE ANALYSIS PIPELINE")

print(f"Original findings: {result['original_count']}")
print(f"Validated findings: {result['validated_count']}")
print(f"Rejected findings: {result['rejected_count']}")

print(f"\nSaved analysis ID: {result['result_id']}")

print("\nVALIDATED FINDINGS")

for index, finding in enumerate(
    result["analysis"].findings, start=1
):
    print(f"\nFinding {index}")
    print(f"Risk: {finding.risk_level}")
    print(f"Evidence: {finding.evidence_quote}")
    print(f"Page: {finding.page_number}")
    print(f"Confidence: {finding.confidence}")

print("\nREJECTED FINDINGS")

for rejected in result["rejected_findings"]:
    print(rejected)
