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

def save_analysis_result(contract_id, analysis_type, result, run_id=None):
    """
    Save an analysis result.

    When run_id is supplied, repeated saves of the same analysis type
    within that run update the existing record instead of duplicating it.

    A new run_id represents a new execution and preserves run history.
    """
    supabase = get_supabase_client()

    result_data = result.model_dump(mode="json")

    record = {
        "contract_id": contract_id,
        "analysis_type": analysis_type,
        "result": result_data,
    }

    if run_id is not None:
        record["run_id"] = str(run_id)

        response = (
            supabase.table("analysis_results")
            .upsert(
                record,
                on_conflict="run_id,analysis_type"
            )
            .execute()
        )
    else:
        # Backward compatibility for existing standalone callers.
        response = (
            supabase.table("analysis_results")
            .insert(record)
            .execute()
        )

    if not response.data:
        raise RuntimeError("Analysis result persistence returned no record.")

    return response.data[0]["id"]
