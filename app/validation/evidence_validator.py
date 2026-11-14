
import re

from pydantic import BaseModel

from app.database import get_supabase_client


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def validate_analysis_evidence(
    contract_id: str,
    analysis: BaseModel,
) -> tuple[BaseModel, list[dict]]:

    supabase = get_supabase_client()

    response = (
        supabase.table("contract_pages")
        .select("page_number, content")
        .eq("contract_id", contract_id)
        .execute()
    )

    pages = {
        page["page_number"]: normalize_text(page["content"])
        for page in response.data
    }

    validated_findings = []
    rejected_findings = []

    for finding in analysis.findings:

        page_content = pages.get(finding.page_number)

        if page_content is None:
            reason = "Referenced page does not exist."
        else:
            quote = normalize_text(finding.evidence_quote)

            if not quote:
                reason = "Evidence quotation is empty."
            elif quote not in page_content:
                reason = "Evidence quotation could not be verified."
            else:
                validated_findings.append(finding)
                continue

        rejected_findings.append({
            "finding": finding.finding,
            "evidence_quote": finding.evidence_quote,
            "page_number": finding.page_number,
            "reason": reason,
        })

    validated_analysis = analysis.model_copy(
        update={"findings": validated_findings}
    )

    return validated_analysis, rejected_findings
