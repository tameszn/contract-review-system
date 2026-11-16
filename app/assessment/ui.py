
import streamlit as st


def render_assessment(assessment, execution_metadata=None):
    execution_metadata = execution_metadata or {}

    st.divider()
    st.header("Contract Risk Assessment")

    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Risk", assessment.overall_risk_level.upper())
    col2.metric("Risk Score", assessment.overall_score)
    col3.metric("Total Findings", len(assessment.ranked_findings))

    st.subheader("Executive Summary")
    st.write(assessment.summary.executive_summary)

    st.subheader("Category Risk Breakdown")

    if assessment.category_scores:
        cols = st.columns(min(3, len(assessment.category_scores)))
        for index, category in enumerate(assessment.category_scores):
            with cols[index % len(cols)]:
                st.metric(category.category, category.score)
                st.caption(
                    f"Risk: {category.risk_level.upper()} | "
                    f"Findings: {category.finding_count}"
                )
    else:
        st.info("No category scores available.")

    st.subheader("Agent Coverage")

    for agent in assessment.coverage:
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            col1.write(f"**{agent.agent_name.replace('_', ' ').title()}**")
            col2.write(agent.status.upper())
            col3.write(f"Findings: {agent.finding_count}")
            if agent.error:
                st.warning(agent.error)

    if execution_metadata:
        with st.expander("Execution Details"):
            st.write(f"Run ID: `{execution_metadata.get('run_id', 'N/A')}`")
            st.write(f"Gate: {execution_metadata.get('gate_decision', 'N/A')}")
            st.write(f"Total Attempts: {execution_metadata.get('total_attempts', 'N/A')}")
            st.json(execution_metadata)

    st.subheader("Ranked Findings")

    if not assessment.ranked_findings:
        st.success("No validated findings were identified.")
    else:
        for index, finding in enumerate(assessment.ranked_findings, start=1):
            title = (
                f"{index}. [{finding.risk_level.upper()}] "
                f"{finding.category}"
            )

            with st.expander(title):
                st.write(finding.finding)
                st.markdown("**Evidence**")
                st.write(f'"{finding.evidence_quote}"')
                st.caption(f"Page: {finding.page_number}")

                st.markdown("**Rationale**")
                st.write(finding.rationale)

                st.markdown("**Recommendation**")
                st.write(finding.recommendation)

                st.caption(
                    f"Confidence: {finding.confidence:.0%} | "
                    f"Sources: {', '.join(finding.source_agents)}"
                )

                if finding.financial_impact:
                    st.write(f"**Financial Impact:** {finding.financial_impact}")

                if finding.applicable_requirement:
                    st.write(
                        f"**Applicable Requirement:** "
                        f"{finding.applicable_requirement}"
                    )

                if finding.requires_review:
                    st.warning(
                        finding.review_reason or "Manual review required."
                    )

    st.subheader("Priority Recommendations")

    priorities = assessment.summary.priorities
    if priorities:
        for priority in priorities:
            st.write(
                f"**Priority {priority.priority_rank}:** "
                f"{priority.recommendation}"
            )
    else:
        st.info("No priority recommendations available.")

    st.subheader("Items Requiring Review")

    if assessment.review_items:
        for item in assessment.review_items:
            st.warning(item)
    else:
        st.success("No additional review items.")
