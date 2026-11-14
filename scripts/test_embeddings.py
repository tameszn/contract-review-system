
from app.embeddings import (
    generate_embeddings,
    generate_query_embedding,
)

texts = [
    "The borrower shall repay the loan within thirty days.",
    "The agreement may be terminated by either party.",
    "The borrower must maintain adequate insurance coverage.",
]

# Generate document embeddings
embeddings = generate_embeddings(texts)

print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))

# Generate a search query embedding
query_embedding = generate_query_embedding(
    "What are the borrower's repayment obligations?"
)

print("Query embedding dimensions:", len(query_embedding))
print("First five values:", query_embedding[:5])

# Verify vector normalization
print(
    "Vector magnitude:",
    sum(value ** 2 for value in embeddings[0]) ** 0.5
)
