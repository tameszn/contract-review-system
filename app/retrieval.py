
from app.database import get_supabase_client
from app.embeddings import generate_query_embedding


def retrieve_relevant_chunks(
    query: str,
    contract_id: str,
    match_threshold: float = 0.50,
    match_count: int = 5,
) -> list[dict]:

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not contract_id.strip():
        raise ValueError("Contract ID cannot be empty.")

    # Generate query embedding
    query_embedding = generate_query_embedding(query)

    # Search Supabase
    supabase = get_supabase_client()

    response = supabase.rpc(
        "match_contract_chunks",
        {
            "query_embedding": query_embedding,
            "target_contract_id": contract_id,
            "match_threshold": match_threshold,
            "match_count": match_count,
        },
    ).execute()

    return response.data
