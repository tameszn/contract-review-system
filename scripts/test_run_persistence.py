
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import get_supabase_client
from app.repo import (
    save_analysis_result,
    start_assessment_run,
    finish_assessment_run,
)
from app.schemas import RiskAssessment, AssessmentSummary


def main():
    contract_id = input("Enter an existing contract UUID: ").strip()
    run_id = str(uuid4())
    supabase = get_supabase_client()

    assessment = RiskAssessment(
        overall_risk_level="low",
        overall_score=0,
        category_scores=[],
        ranked_findings=[],
        summary=AssessmentSummary(
            executive_summary="Persistence verification test.",
            priorities=[],
        ),
        review_items=[],
        coverage=[],
    )

    try:
        start_assessment_run(contract_id, run_id)

        first_id = save_analysis_result(
            contract_id, "risk_assessment", assessment, run_id=run_id
        )
        second_id = save_analysis_result(
            contract_id, "risk_assessment", assessment, run_id=run_id
        )

        assert first_id == second_id, "Upsert created a different result ID."

        results = (
            supabase.table("analysis_results")
            .select("id, contract_id, run_id, analysis_type")
            .eq("run_id", run_id)
            .eq("analysis_type", "risk_assessment")
            .execute()
        )

        assert len(results.data) == 1, (
            f"Expected one analysis row, found {len(results.data)}."
        )
        assert results.data[0]["contract_id"] == contract_id

        finish_assessment_run(
            run_id=run_id,
            status="completed",
            execution_metadata={
                "test": True,
                "result_id": first_id,
            },
            gate_decision="continue",
        )

        run = (
            supabase.table("assessment_runs")
            .select("*")
            .eq("run_id", run_id)
            .single()
            .execute()
        ).data

        assert run["status"] == "completed"
        assert run["contract_id"] == contract_id
        assert run["gate_decision"] == "continue"
        assert run["execution_metadata"]["result_id"] == first_id

        print("PASS: Run Log creation and finalization")
        print("PASS: Analysis result upsert idempotency")
        print("PASS: Exactly one analysis row for this run")
        print("PASS: Run ID and contract ID consistency")
        print(f"Run ID: {run_id}")
        print(f"Result ID: {first_id}")

    finally:
        supabase.table("analysis_results").delete().eq(
            "run_id", run_id
        ).execute()
        supabase.table("assessment_runs").delete().eq(
            "run_id", run_id
        ).execute()


if __name__ == "__main__":
    main()
