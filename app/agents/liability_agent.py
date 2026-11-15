
from app.llm import get_llm
from app.schemas import LiabilityAnalysis
from app.retrieval import retrieve_relevant_chunks


def analyze_liability(
    contract_id: str,
    query: str = "Identify liability risks, indemnification obligations, limitations of liability, and exclusions of damages.",
    match_count: int = 10,
) -> LiabilityAnalysis:

    chunks = retrieve_relevant_chunks(
        query=query,
        contract_id=contract_id,
        match_threshold=0.35,
        match_count=match_count,
    )

    if not chunks:
        raise ValueError("No relevant contract passages found.")

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
    structured_llm = llm.with_structured_output(LiabilityAnalysis)

    prompt = f"""
    You are a contract liability analysis specialist.

    Analyze the supplied contract passages for potential liability risks.

    Examine:
    - Limitation of liability
    - Indemnification obligations
    - Exclusion of damages
    - Unlimited or uncapped liability
    - Asymmetric liability obligations
    - Unclear or unusually broad liability provisions

    STRICT RULES:
    1. Base every finding exclusively on the supplied contract passages.
    2. Evidence quotes must be exact excerpts copied from the supplied text.
    3. Never invent clause wording, page numbers, or contractual obligations.
    4. Use the page number attached to the passage containing the evidence.
    5. Do not treat the absence of a clause in the retrieved passages as proof
       that the entire contract lacks that clause.
    6. Distinguish actual contractual wording from your interpretation.
    7. If no meaningful liability risks are identified, return an empty findings list.
    8. Risk levels must be low, medium, high, or critical.
    9. Confidence must be between 0 and 1.
    10. Provide practical recommendations without presenting them as legal advice.
    11.The risk_level MUST be exactly one of:
        low, medium, high, critical.
    
        Do not use alternative labels such as moderate, severe, or extreme.

    CONTRACT PASSAGES:
    {context}
    """

    return structured_llm.invoke(prompt)
