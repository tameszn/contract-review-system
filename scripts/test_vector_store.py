
from app.vector_store import embed_contract_chunks

contract_id = input("Enter contract ID: ").strip()

if not contract_id:
    raise ValueError("Contract ID cannot be empty.")

count = embed_contract_chunks(contract_id)

print(f"Successfully generated and stored {count} embeddings.")
