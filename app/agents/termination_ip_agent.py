from app.llm import get_llm
from app.schemas import TerminationIPAnalysis
from app.retrieval import retrieve_relevant_chunks


def analyze_termination_ip(
    contract_id: str,
    query: str = (
        "Identify termination rights, termination conditions, "
        "notice periods, automatic renewal, early termination "
        "penalties, intellectual property ownership, licensing, "
        "IP transfer restrictions, confidentiality obligations "
        "and obligations that survive termination."
    ),
    match_count: int = 15,
) -> TerminationIPAnalysis:

    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    chunks = retrieve_relevant_chunks(
        query=query,
        contract_id=contract_id,
        match_threshold=0.35,
        match_count=match_count,
    )

    if not chunks:
        raise ValueError("No relevant termination or IP passages found.")

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
    structured_llm = llm.with_structured_output(TerminationIPAnalysis)

    prompt = f"""
    You are a contract termination and intellectual property risk analyst.

    Analyze the supplied contract passages for risks involving:

    1. Termination rights and conditions.
    2. Notice periods and termination procedures.
    3. Automatic renewal and renewal restrictions.
    4. Early termination fees or penalties.
    5. Intellectual property ownership and assignment.
    6. Licensing scope, restrictions and sublicensing.
    7. Use of pre-existing and newly developed IP.
    8. Confidentiality obligations after termination.
    9. Survival clauses and post-termination obligations.
    10. Unilateral or asymmetric termination rights.

    CONTRACT PASSAGES:
    {context}

    RULES:
    - Identify only issues supported by the supplied passages.
    - Evidence quotes must be exact excerpts from the contract.
    - Use the correct original PDF page number.
    - Never invent deadlines, ownership rights, fees or obligations.
    - Distinguish explicit contractual risks from potential ambiguity.
    - Do not treat an absent provision as proof of a breach.
    - Provide practical recommendations.
    - Use risk levels: low, medium, high or critical.
    - Confidence must be between 0.0 and 1.0.
    - If no meaningful risks are found, return an empty findings list.
    -The risk_level MUST be exactly one of:
        low, medium, high, critical.
    
        Do not use alternative labels such as moderate, severe, or extreme.

    Provide an overall assessment and structured findings.
    """

    return structured_llm.invoke(prompt)