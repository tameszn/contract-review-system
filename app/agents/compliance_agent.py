from app.llm import get_llm
from app.schemas import ComplianceAnalysis
from app.retrieval import retrieve_relevant_chunks


def analyze_compliance(
    contract_id: str,
    query: str = (
        "Identify data protection, privacy, confidentiality, "
        "information security, regulatory compliance, statutory "
        "obligations, audit rights, anti-bribery, sanctions, "
        "licensing and industry-specific compliance provisions."
    ),
    match_count: int = 15,
) -> ComplianceAnalysis:

    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    chunks = retrieve_relevant_chunks(
        query=query,
        contract_id=contract_id,
        match_threshold=0.35,
        match_count=match_count,
    )

    if not chunks:
        raise ValueError("No relevant compliance passages found.")

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
    structured_llm = llm.with_structured_output(ComplianceAnalysis)

    prompt = f"""
    You are a contract compliance risk analyst.

    Analyze the supplied contract passages for:

    1. Data protection and privacy obligations.
    2. Confidentiality and information security.
    3. Regulatory and statutory compliance obligations.
    4. Audit rights and compliance reporting.
    5. Licensing, permits and certifications.
    6. Anti-bribery and anti-corruption obligations.
    7. Sanctions and restricted-party obligations.
    8. Employment and labour-related compliance, where applicable.
    9. Industry-specific compliance requirements.

    CONTRACT PASSAGES:
    {context}

    RULES:

    - Identify only issues supported by the supplied passages.
    - Evidence quotes must be exact excerpts from the contract.
    - Use the correct original PDF page number.
    - Do not invent regulatory requirements or legal obligations.
    - Do not assume a particular jurisdiction unless specified.
    - Distinguish contractual obligations from statutory requirements.
    - Do not declare a legal violation without sufficient evidence.
    - Explain the applicable requirement and why it matters.
    - Flag ambiguity and missing safeguards as potential risks,
      not confirmed violations.
    - Use risk levels: low, medium, high or critical.
    - Confidence must be between 0.0 and 1.0.
    - If no meaningful risks are found, return an empty findings list.

    Provide an overall assessment and structured findings.
    """

    return structured_llm.invoke(prompt)