
from app.assessment.graph import run_graph_assessment


def main():
    contract_id = input("Enter an existing processed contract UUID: ").strip()

    if not contract_id:
        raise ValueError("Contract ID cannot be empty.")

    print("\nStarting assessment...")
   

    try:
        result = run_graph_assessment(contract_id)

        assessment = result["assessment"]
        metadata = result["execution_metadata"]

        print("\n========== ASSESSMENT RESULT ==========")
        print(f"Run ID: {metadata['run_id']}")
        print(f"Result ID: {result['result_id']}")
        print(f"Overall Risk: {assessment.overall_risk_level}")
        print(f"Overall Score: {assessment.overall_score}")
        print(f"Total Findings: {len(assessment.ranked_findings)}")
        print(f"Gate Decision: {metadata.get('gate_decision')}")
        print(f"Retry Round: {metadata.get('retry_round')}")
        print(f"Total Agent Attempts: {metadata.get('total_attempts')}")

        print("\n========== AGENT COVERAGE ==========")
        for agent, status in metadata["agent_statuses"].items():
            agent_data = metadata["agent_metadata"].get(agent, {})
            print(
                f"{agent}: {status} | "
                f"Attempts: {agent_data.get('attempts', 0)} | "
                f"Validated: {agent_data.get('validated_count', 0)}"
            )

        print("\n========== SUMMARY ==========")
        print(assessment.summary.executive_summary)

        print("\n========== REVIEW ITEMS ==========")
        for item in assessment.review_items:
            print(f"- {item}")

        print("\n========== LIVE TEST COMPLETED ==========")

    except Exception as exc:
        print("\nLIVE ASSESSMENT FAILED")
        print(f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
