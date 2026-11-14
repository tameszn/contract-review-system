
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model once and reuse it.
    """
    return SentenceTransformer(MODEL_NAME)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text passages into embeddings.
    """

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    if embeddings.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"got {embeddings.shape[1]}"
        )

    return embeddings.tolist()


def generate_query_embedding(query: str) -> list[float]:
    """
    Generate an embedding for a semantic search query.
    """

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    query_text = (
        "Represent this sentence for searching relevant passages: "
        + query
    )

    return generate_embeddings([query_text])[0]
