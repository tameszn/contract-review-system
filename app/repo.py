from app.database import get_supabase_client
from datetime import datetime, timezone
from app.embeddings import generate_embeddings


def save_contract(filename, pages, chunks):
    supabase = get_supabase_client()
    contract_id = None

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

        # 3. Generate embeddings for all chunks
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = generate_embeddings(chunk_texts)

        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count does not match chunk count.")

        # 4. Save chunks with their embeddings
        chunk_records = [
            {
                "contract_id": contract_id,
                "page_number": chunk.page,
                "chunk_index": index,
                "content": chunk.text,
                "section": chunk.section,
                "embedding": embedding
            }
            for index, (chunk, embedding) in enumerate(
                zip(chunks, embeddings)
            )
        ]

        if chunk_records:
            supabase.table("contract_chunks").insert(
                chunk_records
            ).execute()

        return contract_id

    except Exception:
        # Remove partially saved contract and dependent records
        if contract_id is not None:
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


# run logs


def start_assessment_run(contract_id: str, run_id: str):
    supabase = get_supabase_client()
    response = supabase.table("assessment_runs").insert({
        "run_id": run_id,
        "contract_id": contract_id,
        "status": "running",
    }).execute()

    if not response.data:
        raise RuntimeError("Failed to create assessment run log.")

    return response.data[0]


def finish_assessment_run(
    run_id: str,
    status: str,
    execution_metadata: dict,
    gate_decision: str | None = None,
    error: str | None = None,
):
    if status not in {"completed", "partial", "failed"}:
        raise ValueError(f"Invalid final run status: {status}")

    supabase = get_supabase_client()
    response = supabase.table("assessment_runs").update({
        "status": status,
        "gate_decision": gate_decision,
        "execution_metadata": execution_metadata,
        "error": error,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("run_id", run_id).execute()

    if not response.data:
        raise RuntimeError(f"Failed to finalize run log: {run_id}")

    return response.data[0]
