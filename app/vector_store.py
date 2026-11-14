
from app.database import get_supabase_client
from app.embeddings import generate_embeddings


def embed_contract_chunks(contract_id: str) -> int:
    """
    Generate and store embeddings for all chunks
    belonging to a contract.
    """

    supabase = get_supabase_client()

    # Fetch existing chunks
    response = (
        supabase.table("contract_chunks")
        .select("id, chunk_index, content")
        .eq("contract_id", contract_id)
        .order("chunk_index")
        .execute()
    )

    chunks = response.data

    if not chunks:
        raise ValueError(
            f"No chunks found for contract: {contract_id}"
        )

    # Generate embeddings
    texts = [chunk["content"] for chunk in chunks]

    embeddings = generate_embeddings(texts)

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count.")

    # Update existing records using their IDs
    for chunk, embedding in zip(chunks, embeddings):
     (
        supabase.table("contract_chunks")
        .update({"embedding": embedding})
        .eq("id", chunk["id"])
        .execute()
     )

    return len(chunks)
