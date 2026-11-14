
from app.retrieval import retrieve_relevant_chunks

contract_id = input("Enter contract ID: ").strip()

query = input("Enter your contract question: ").strip()

results = retrieve_relevant_chunks(
    query=query,
    contract_id=contract_id,
    match_threshold=0.50,
    match_count=5,
)

if not results:
    print("\nNo relevant passages found.")

else:
    print(f"\nRetrieved {len(results)} relevant passages.")

    for index, result in enumerate(results, start=1):

        print(f"\n{'=' * 50}")
        print(f"Result {index}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Page: {result['page_number']}")
        print(f"Section: {result['section']}")
        print(f"Content:\n{result['content']}")
