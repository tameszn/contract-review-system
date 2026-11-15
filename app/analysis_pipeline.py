
from app.agents.liability_agent import analyze_liability
from app.validation.evidence_validator import validate_analysis_evidence
from app.repo import save_analysis_result
from app.agents.termination_ip_agent import analyze_termination_ip
from app.agents.compliance_agent import analyze_compliance


def run_liability_analysis(contract_id: str) -> dict:
    """
    Run liability analysis, validate its evidence,
    and persist only verified findings.
    """

    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    # 1. Generate liability analysis
    analysis = analyze_liability(contract_id)

    # 2. Validate evidence against original contract pages
    validated_analysis, rejected_findings = (
        validate_analysis_evidence(
            contract_id=contract_id,
            analysis=analysis,
        )
    )

    # 3. Persist validated analysis
    result_id = save_analysis_result(
        contract_id=contract_id,
        analysis_type="liability_analysis",
        result=validated_analysis,
    )

    return {
        "analysis": validated_analysis,
        "rejected_findings": rejected_findings,
        "result_id": result_id,
        "original_count": len(analysis.findings),
        "validated_count": len(validated_analysis.findings),
        "rejected_count": len(rejected_findings),
    }

def run_termination_ip_analysis(contract_id: str) -> dict:
    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    analysis = analyze_termination_ip(contract_id)

    validated_analysis, rejected_findings = validate_analysis_evidence(
        contract_id=contract_id,
        analysis=analysis,
    )

    result_id = save_analysis_result(
        contract_id=contract_id,
        analysis_type="termination_ip_analysis",
        result=validated_analysis,
    )

    return {
        "analysis": validated_analysis,
        "rejected_findings": rejected_findings,
        "result_id": result_id,
        "original_count": len(analysis.findings),
        "validated_count": len(validated_analysis.findings),
        "rejected_count": len(rejected_findings),
    }

def run_compliance_analysis(contract_id: str) -> dict:
    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    analysis = analyze_compliance(contract_id)

    validated_analysis, rejected_findings = validate_analysis_evidence(
        contract_id=contract_id,
        analysis=analysis,
    )

    result_id = save_analysis_result(
        contract_id=contract_id,
        analysis_type="compliance_analysis",
        result=validated_analysis,
    )

    return {
        "analysis": validated_analysis,
        "rejected_findings": rejected_findings,
        "result_id": result_id,
        "original_count": len(analysis.findings),
        "validated_count": len(validated_analysis.findings),
        "rejected_count": len(rejected_findings),
    }