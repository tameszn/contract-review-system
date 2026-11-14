from app.database import get_supabase_client


def save_contract(filename, pages, chunks):
    supabase = get_supabase_client()

    try:
        # 1. Save contract metadata
        contract_response = supabase.table("contracts").insert({
            "filename": filename,
            "file_type": "pdf",
            "page_count": len(pages),
            "status": "processed"
        }).execute()

        contract_id = contract_response.data[0]["id"]

        # 2. Save extracted pages
        page_records = [
            {
                "contract_id": contract_id,
                "page_number": page["page"],
                "content": page["text"],
                "is_scanned": page["is_scanned"]
            }
            for page in pages
        ]

        if page_records:
            supabase.table("contract_pages").insert(
                page_records
            ).execute()

        # 3. Save chunks
        chunk_records = [
            {
                "contract_id": contract_id,
                "page_number": chunk.page,
                "chunk_index": index,
                "content": chunk.text,
                "section": chunk.section
            }
            for index, chunk in enumerate(chunks)
        ]

        if chunk_records:
            supabase.table("contract_chunks").insert(
                chunk_records
            ).execute()

        return contract_id

    except Exception:
        # Remove partially saved contract and its dependent records
        if "contract_id" in locals():
            supabase.table("contracts").delete().eq(
                "id", contract_id
            ).execute()

        raise

def save_analysis_result(contract_id, analysis_type, result):
    supabase = get_supabase_client()

    result_data = result.model_dump(mode="json")

    response = supabase.table("analysis_results").insert({
        "contract_id": contract_id,
        "analysis_type": analysis_type,
        "result": result_data
    }).execute()

    return response.data[0]["id"]    