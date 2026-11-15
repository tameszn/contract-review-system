
from typing import Any, TypedDict


class AssessmentGraphState(TypedDict, total=False):
    # Contract identifier
    contract_id: str

    # Validated specialist analyses
    liability_analysis: Any
    financial_analysis: Any
    termination_ip_analysis: Any
    compliance_analysis: Any

    # Individual execution statuses
    liability_status: str
    financial_status: str
    termination_ip_status: str
    compliance_status: str

    # Individual execution errors
    liability_error: str | None
    financial_error: str | None
    termination_ip_error: str | None
    compliance_error: str | None

    # Execution metadata
    liability_metadata: dict
    financial_metadata: dict
    termination_ip_metadata: dict
    compliance_metadata: dict

    # Final outputs
    assessment: Any
    result_id: str
    execution_metadata: dict
