from app.llm import get_llm
from app.schemas import ContractExtraction
from app.schemas import (
    ContractExtraction,
    ContractMetadata,
    ContractParty,
    ExtractedClause,
)


def extract_contract_data(text: str, page_number: int) -> ContractExtraction:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        ContractExtraction
    )

    prompt = f"""
    You are a contract information extraction system.

    Extract the contract metadata and clauses from the
    provided contract text.

    Rules:
    1. Only extract information explicitly present in the text.
    2. Do not invent or assume missing information.
    3. Use null for unavailable metadata.
    4. Preserve the original wording of extracted clauses.
    5. Extract only clauses actually present in the text.
    6. The supplied page number is authoritative.
    7. Do not provide legal opinions or risk assessments.
    8. All dates must use ISO 8601 format: YYYY-MM-DD.
    9. Convert dates written in natural language into YYYY-MM-DD.
    10. If a date is ambiguous or cannot be reliably determined, return null. 
    11. The parties field must always be an array.
    Return [] when no parties are identified.
    Never return null for parties.

    PAGE NUMBER: {page_number}

    CONTRACT TEXT:
    {text}
    """

    return structured_llm.invoke(prompt)


def consolidate_extraction(
    page_results: list[ContractExtraction]
) -> ContractExtraction:

    metadata_data = {}
    parties = {}
    clauses = {}

    metadata_fields = [
        "title",
        "contract_type",
        "effective_date",
        "expiry_date",
        "jurisdiction",
        "contract_value",
        "payment_terms",
    ]

    for result in page_results:

        # Merge metadata: retain the first available value.
        for field in metadata_fields:
            value = getattr(result.metadata, field)

            if metadata_data.get(field) is None and value is not None:
                metadata_data[field] = value

        # Merge parties by name.
        for party in result.metadata.parties or []:
            key = (party.name or "").strip().lower()

            if not key:
                key = f"{party.role}:{party.address}".lower()

            if key not in parties:
                parties[key] = party
            else:
                existing = parties[key]

                parties[key] = ContractParty(
                    name=existing.name or party.name,
                    role=existing.role or party.role,
                    address=existing.address or party.address,
                )

        # Preserve clauses and their original page numbers.
        for clause in result.clauses:
            key = (
                clause.clause_type,
                clause.clause_title,
                clause.clause_text,
                clause.page_number,
            )

            clauses[key] = clause

    return ContractExtraction(
        metadata=ContractMetadata(
            **metadata_data,
            parties=list(parties.values()),
        ),
        clauses=list(clauses.values()),
    )