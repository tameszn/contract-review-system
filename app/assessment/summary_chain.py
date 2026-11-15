
import json

from langchain_core.prompts import ChatPromptTemplate

from app.llm import get_llm
from app.schemas import AssessmentSummary, ConsolidatedFinding


SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are the executive assessment summarizer for a contract
risk assessment system.

Your task is to summarize ONLY the consolidated findings supplied
in the input.

Rules:
1. Do not assume or invent facts not present in the findings.
2. Do not introduce risks that are not represented by the findings.
3. Do not modify or reinterpret the supplied risk levels.
4. Write a concise, professional executive summary.
5. Prioritize recommendations by their practical importance,
   considering risk level, confidence, and potential impact.
6. Every priority recommendation must reference an existing
   finding_id from the input.
7. Use the finding's recommendation as the basis for your advice.
8. Do not create new finding IDs.
9. Do not provide generic recommendations unrelated to a finding.
10. If a finding needs human review, do not present its interpretation
    as conclusively established.
11. Keep recommendations specific and actionable.
12. Do not provide legal conclusions beyond the supplied evidence.

Return data matching the AssessmentSummary schema.
            """,
        ),
        (
            "human",
            """
Summarize the following consolidated contract findings.

CONSOLIDATED FINDINGS:
{findings_json}
            """,
        ),
    ]
)


def prepare_findings_payload(
    findings: list[ConsolidatedFinding],
) -> list[dict]:
    """
    Prepare the limited data that the summary LLM is allowed to see.

    Raw contract text and unvalidated agent outputs are never included.
    """

    payload = []

    for finding in findings:
        payload.append(
            {
                "finding_id": finding.finding_id,
                "source_agents": finding.source_agents,
                "category": finding.category,
                "risk_level": finding.risk_level,
                "finding": finding.finding,
                "evidence_quote": finding.evidence_quote,
                "page_number": finding.page_number,
                "rationale": finding.rationale,
                "recommendation": finding.recommendation,
                "confidence": finding.confidence,
                "financial_impact": finding.financial_impact,
                "applicable_requirement": finding.applicable_requirement,
                "requires_review": finding.requires_review,
                "review_reason": finding.review_reason,
            }
        )

    return payload


def validate_summary_references(
    summary: AssessmentSummary,
    findings: list[ConsolidatedFinding],
) -> AssessmentSummary:
    """
    Ensure that all LLM-generated priority recommendations refer
    to valid findings and have unique, sequential priority ranks.
    """

    valid_finding_ids = {
        finding.finding_id for finding in findings
    }

    used_finding_ids = set()
    used_priority_ranks = set()

    for priority in summary.priorities:

        if priority.finding_id not in valid_finding_ids:
            raise ValueError(
                "Summary references an unknown finding ID: "
                f"{priority.finding_id}"
            )

        if priority.finding_id in used_finding_ids:
            raise ValueError(
                "Summary contains duplicate priority recommendations "
                f"for finding ID: {priority.finding_id}"
            )

        if priority.priority_rank in used_priority_ranks:
            raise ValueError(
                "Summary contains duplicate priority ranks: "
                f"{priority.priority_rank}"
            )

        used_finding_ids.add(priority.finding_id)
        used_priority_ranks.add(priority.priority_rank)

    expected_ranks = set(range(1, len(summary.priorities) + 1))

    if used_priority_ranks != expected_ranks:
        raise ValueError(
            "Priority ranks must be sequential, starting from 1."
        )

    return summary.model_copy(
        update={
            "priorities": sorted(
                summary.priorities,
                key=lambda item: item.priority_rank,
            )
        }
    )


def generate_assessment_summary(
    findings: list[ConsolidatedFinding],
) -> AssessmentSummary:
    """
    Generate an executive summary and prioritized recommendations
    from consolidated, evidence-validated findings.

    One structured LLM call is made when findings are present.
    """

    if not findings:
        return AssessmentSummary(
            executive_summary=(
                "No evidence-validated material risks were identified "
                "by the completed specialist analyses. This does not "
                "necessarily establish that the contract is risk-free."
            ),
            priorities=[],
        )

    finding_ids = [
        finding.finding_id for finding in findings
    ]

    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError(
            "Consolidated findings contain duplicate finding IDs."
        )

    findings_payload = prepare_findings_payload(findings)

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        AssessmentSummary
    )

    summary_chain = SUMMARY_PROMPT | structured_llm

    summary = summary_chain.invoke(
        {
            "findings_json": json.dumps(
                findings_payload,
                ensure_ascii=False,
                indent=2,
            )
        }
    )

    if not isinstance(summary, AssessmentSummary):
        summary = AssessmentSummary.model_validate(summary)

    return validate_summary_references(summary, findings)
