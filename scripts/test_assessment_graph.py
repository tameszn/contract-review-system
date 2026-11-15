
import sys

from app.assessment.graph import run_graph_assessment


def main():

    if len(sys.argv) != 2:
        print(
            "Usage: python -m scripts.test_assessment_graph "
            "<contract_uuid>"
        )
        return

    contract_id = sys.argv[1]

    print(f"Starting assessment for contract {contract_id}...\n")

    result = run_graph_assessment(contract_id)

    assessment = result["assessment"]

    print("\n========== CONTRACT ASSESSMENT ==========")

    print("Result ID:", result["result_id"])

    print("\nOverall risk:")
    print("Level:", assessment.overall_risk_level)
    print("Score:", assessment.overall_score)

    print("\nCategory scores:")

    for category in assessment.category_scores:
        print(
            f"{category.category}: "
            f"{category.score} ({category.risk_level})"
        )

    print("\nExecutive summary:")
    print(assessment.summary.executive_summary)

    print("\nRanked findings:")

    for finding in assessment.ranked_findings:
        print(
            f"\n[{finding.finding_id}] "
            f"{finding.category} | {finding.risk_level}"
        )
        print("Sources:", finding.source_agents)
        print("Page:", finding.page_number)
        print("Finding:", finding.finding)

    print("\nAgent coverage:")

    for agent in assessment.coverage:
        print(
            f"{agent.agent_name}: {agent.status}, "
            f"findings={agent.finding_count}"
        )

        if agent.error:
            print("Error:", agent.error)

    print("\nExecution metadata:")

    for name, metadata in result["execution_metadata"].items():
        print(name, metadata)

    print("\n Assessment completed.")


if __name__ == "__main__":
    main()
