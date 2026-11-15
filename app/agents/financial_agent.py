
from app.llm import get_llm
from app.schemas import FinancialAnalysis
from app.retrieval import retrieve_relevant_chunks


def analyze_financial_terms(
    contract_id: str,
    query: str = (
        "Identify financial obligations, payment terms, "
        "late payment penalties, fees, deposits, refunds, "
        "tax responsibilities, price adjustments and "
        "other financial risks."
    ),
    match_count: int = 15,
) -> FinancialAnalysis:

    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    chunks = retrieve_relevant_chunks(
        query=query,
        contract_id=contract_id,
        match_threshold=0.35,
        match_count=match_count,
    )

    if not chunks:
        raise ValueError("No relevant financial passages found.")

    context = "\n\n".join(
        f"""
        PAGE: {chunk['page_number']}
        SECTION: {chunk['section'] or 'Not specified'}
        CONTENT:
        {chunk['content']}
        """
        for chunk in chunks
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(FinancialAnalysis)

    prompt = f"""
    You are a specialist contract financial analysis system.

    Analyze the supplied contract passages for financial
    obligations, commercial exposure and payment-related risks.

    Examine:
    - Payment deadlines and conditions
    - Late payment interest and penalties
    - Deposits, advances and recurring fees
    - Refunds and cancellation charges
    - Tax allocation and responsibilities
    - Price escalation and adjustment clauses
    - Unclear or potentially excessive financial obligations
    - Financial obligations that are one-sided or asymmetric

    STRICT RULES:

    1. Base every finding exclusively on the supplied passages.
    2. Evidence quotations must be exact excerpts.
    3. Never invent amounts, percentages, currencies or deadlines.
    4. Use the page number attached to the evidence passage.
    5. Distinguish explicit contractual obligations from inferred risks.
    6. Do not calculate financial exposure using unstated assumptions.
    7. Do not assume a financial provision is unfair merely because
       it benefits one party.
    8. Do not treat missing information in retrieved passages as
       proof that the entire contract lacks that information.
    9. If no meaningful financial risks are identified,
       return an empty findings list.
    10. Risk levels must be low, medium, high or critical.
    11. Confidence must be between 0 and 1.
    12. Recommendations must be practical and not presented
        as legal or financial advice.

    CONTRACT PASSAGES:

    {context}
    """

    return structured_llm.invoke(prompt)
