
import tempfile
from pathlib import Path

import streamlit as st

from app.theme import inject_theme, render_hero
from app.pdf_extractor import extract_pages
from app.chunking import build_chunks
from app.repo import save_contract, save_analysis_result
from app.extraction import (
    extract_contract_data,
    consolidate_extraction,
)
from app.assessment.graph import run_graph_assessment
from app.assessment.ui import render_assessment


# --------------------------------------
# Page configuration
# --------------------------------------

st.set_page_config(
    page_title="Contract iQ",
    page_icon="📄",
    layout="wide",
)

inject_theme()
render_hero()


# --------------------------------------
# Session state
# --------------------------------------

if "contract_id" not in st.session_state:
    st.session_state.contract_id = None

if "risk_assessment_result" not in st.session_state:
    st.session_state.risk_assessment_result = None

if "risk_assessment_error" not in st.session_state:
    st.session_state.risk_assessment_error = None


# --------------------------------------
# Application header
# --------------------------------------

st.subheader("Every clause. Every risk. Every page cited")
st.write("AI-powered Contract Intelligence and Review Platform")

st.divider()


# --------------------------------------
# PDF Upload
# --------------------------------------

uploaded_file = st.file_uploader(
    "Upload your contract",
    type=["pdf"],
    accept_multiple_files=False,
)


if uploaded_file is not None:

    st.info(f"Selected file: {uploaded_file.name}")

    if st.button(
        "Process and analyze contract",
        type="primary",
        key="process_contract",
    ):

        temp_pdf_path = None

        try:

            # 1. Save temporary PDF

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf",
            ) as temp_pdf:

                temp_pdf.write(uploaded_file.getbuffer())
                temp_pdf_path = temp_pdf.name

            # 2. Extract PDF pages

            with st.spinner("Extracting PDF pages..."):

                pages = extract_pages(temp_pdf_path)

            if not pages:
                raise ValueError("No pages could be extracted.")

            st.success(f"Extracted {len(pages)} pages.")

            # 3. Generate chunks

            with st.spinner("Generating contract chunks..."):

                chunks = build_chunks(pages)

            st.success(f"Generated {len(chunks)} chunks.")

            # 4. Save contract and embeddings

            with st.spinner("Saving contract to database..."):

                contract_id = save_contract(
                    filename=uploaded_file.name,
                    pages=pages,
                    chunks=chunks,
                )

                st.session_state.contract_id = contract_id
                st.session_state.risk_assessment_result = None
                st.session_state.risk_assessment_error = None

            st.success("Contract successfully saved!")

            st.write(f"**Contract ID:** `{contract_id}`")

            # 5. Extract structured information

            page_results = []

            with st.spinner(
                "Analyzing contract... This might take some minutes."
            ):

                for page in pages:

                    text = page["text"].strip()

                    if not text:
                        continue

                    if page["is_scanned"]:
                        st.warning(
                            f"Page {page['page']} may be scanned "
                            "and contain insufficient extractable text."
                        )

                    result = extract_contract_data(
                        text=text,
                        page_number=page["page"],
                    )

                    page_results.append(result)

            if not page_results:
                raise ValueError(
                    "No structured extraction results were generated."
                )

            # 6. Consolidate extraction results

            with st.spinner("Consolidating contract information..."):

                final_result = consolidate_extraction(page_results)

            # 7. Save extraction results

            with st.spinner("Saving analysis results..."):

                analysis_id = save_analysis_result(
                    contract_id=contract_id,
                    analysis_type="metadata_extraction",
                    result=final_result,
                )

            st.success("Contract analysis completed successfully!")

            # 8. Processing summary

            st.divider()
            st.subheader("Processing Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric("Pages extracted", len(pages))
            col2.metric("Chunks generated", len(chunks))
            col3.metric("Pages analyzed", len(page_results))

            st.write(f"**Contract ID:** `{contract_id}`")
            st.write(f"**Analysis ID:** `{analysis_id}`")

            # 9. Extracted metadata

            st.divider()
            st.subheader("Extracted Contract Metadata")

            st.json(
                final_result.metadata.model_dump(mode="json")
            )

            # 10. Extracted clauses

            st.divider()

            st.subheader(
                f"Extracted Clauses ({len(final_result.clauses)})"
            )

            if final_result.clauses:

                for index, clause in enumerate(
                    final_result.clauses,
                    start=1,
                ):

                    title = (
                        clause.clause_title
                        or clause.clause_type
                    )

                    with st.expander(
                        f"{index}. {title} — Page {clause.page_number}"
                    ):

                        st.write(
                            f"**Clause type:** {clause.clause_type}"
                        )

                        if clause.section:
                            st.write(
                                f"**Section:** {clause.section}"
                            )

                        st.write(clause.clause_text)

            else:
                st.info("No clauses were identified.")

            # 11. Extracted PDF content

            st.divider()
            st.subheader("Extracted PDF Content")

            for page in pages:

                with st.expander(f"Page {page['page']}"):

                    if page["is_scanned"]:
                        st.warning("This page may require OCR.")

                    st.text(page["text"])

        except Exception as e:

            st.error(f"Processing failed: {e}")
            st.exception(e)

        finally:

            if temp_pdf_path:
                Path(temp_pdf_path).unlink(missing_ok=True)


else:
    st.caption("Upload a PDF contract to begin.")


# --------------------------------------
# Contract Risk Assessment
# --------------------------------------

if st.session_state.contract_id:

    st.divider()
    st.subheader("Contract Risk Assessment")

    if st.button(
        "Run Risk Assessment",
        type="primary",
        key="run_risk_assessment",
    ):

        st.session_state.risk_assessment_error = None

        try:

            with st.spinner(
                "Running four specialist agents... Please wait."
            ):

                result = run_graph_assessment(
                    st.session_state.contract_id
                )

            st.session_state.risk_assessment_result = result

        except Exception as e:

            st.session_state.risk_assessment_result = None
            st.session_state.risk_assessment_error = str(e)

    # Display assessment errors

    if st.session_state.risk_assessment_error:

        st.error(
            f"Risk assessment failed: "
            f"{st.session_state.risk_assessment_error}"
        )

    # Display completed assessment

    if st.session_state.risk_assessment_result:

        result = st.session_state.risk_assessment_result

        render_assessment(
            result["assessment"],
            result.get("execution_metadata"),
        )
