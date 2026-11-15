
import sys

from app.assessment.pipeline import run_unified_assessment


def main():

    if len(sys.argv) != 2:
        print(
            "Usage: python -m scripts.test_unified_assessment "
            "<contract_uuid>"
        )
        return

    contract_id = sys.argv[1]

    print("Starting  contract assessment...\n")

    result = run_unified_assessment(contract_id)

    assessment = result["assessment"]

    print("\n========== ASSESSMENT RESULT ==========")

    print("Result ID:", result["result_id"])

    print("\nOverall risk:")
    print("Level:", assessment.overall_risk_level)
    print("Score:", assessment.overall_score)

    print("\nCategory scores:")

    for category in assessment.category_scores:
        print(
            f"{category.category}: "
            f"{category.score} "
            f"({category.risk_level})"
        )

    print("\nExecutive summary:")
    print(assessment.summary.executive_summary)

    print("\n findings:")

    for finding in assessment.ranked_findings:
        print(f"\nID: {finding.finding_id}")
        print("Category:", finding.category)
        print("Severity:", finding.risk_level)
        print("Source agents:", finding.source_agents)
        print("Page:", finding.page_number)
        print("Finding:", finding.finding)
        print("Evidence:", finding.evidence_quote)

    print("\nPriority recommendations:")

    for priority in assessment.summary.priorities:
        print(
            f"{priority.priority_rank}. "
            f"[{priority.finding_id}] "
            f"{priority.recommendation}"
        )

    print("\nHuman review items:")

    for item in assessment.review_items:
        print("-", item)

    print("\nAgent coverage:")

    for agent in assessment.coverage:
        print(
            f"{agent.agent_name}: "
            f"{agent.status}, "
            f"findings={agent.finding_count}"
        )

        if agent.error:
            print("  Error:", agent.error)

    print("\nExecution metadata:")

    for agent_name, metadata in result["execution_metadata"].items():
        print(agent_name, metadata)

    print("\n assessment completed,Contract analysis saved to database.")


if __name__ == "__main__":
    main()
