from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from app.shared import reset_directory, save_uploaded_files

from src.prototype2.pipeline import run_prototype2_pipeline


APP_INPUT_DIR = Path("data/inputs/narratives_app")


def render_section_card(section: dict) -> None:
    with st.container(border=True):
        st.markdown(f"### {section['title']}")
        st.write(section["narrative_text"])

        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Category: {section['category']}")
            st.caption(f"Evidence items: {section['evidence_count']}")
        with col2:
            st.caption(f"Grounded: {section['grounded']}")
            st.caption(
                "Source documents: "
                + (", ".join(section["source_documents"]) if section["source_documents"] else "None")
            )

        with st.expander("Show source chunk IDs", expanded=False):
            if section["source_chunk_ids"]:
                for chunk_id in section["source_chunk_ids"]:
                    st.code(chunk_id)
            else:
                st.write("No source chunk IDs available.")


st.set_page_config(page_title="Prototype 2 - Narrative Analysis", layout="wide")

st.title("Prototype 2: Narrative Analysis and Drafting")
st.write(
    """
Upload one or more narrative report files to generate grounded MEL-style draft sections.
This workflow segments reports, routes evidence into reporting categories, and produces a structured draft.
"""
)

with st.expander("What this page does", expanded=False):
    st.markdown(
        """
- Loads uploaded narrative documents  
- Splits reports into paragraph-level chunks  
- Routes chunks into MEL-relevant categories  
- Builds evidence bundles with source traceability  
- Produces grounded draft report sections  
"""
    )

uploaded_files = st.file_uploader(
    "Upload narrative reports (.txt or .md)",
    type=["txt", "md"],
    accept_multiple_files=True,
)

run_button = st.button("Run Narrative Pipeline", type="primary")

if run_button:
    if not uploaded_files:
        st.error("Please upload at least one narrative file.")
    else:
        try:
            reset_directory(APP_INPUT_DIR)
            saved_files = save_uploaded_files(uploaded_files, APP_INPUT_DIR)

            with st.spinner("Running Prototype 2 pipeline..."):
                result = run_prototype2_pipeline(input_dir=APP_INPUT_DIR)
                ui_summary = result["ui_summary"]

            st.success("Prototype 2 pipeline completed successfully.")

            st.subheader("Run Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Documents", ui_summary["metadata"]["document_count"])
            col2.metric("Chunks", ui_summary["metadata"]["chunk_count"])
            col3.metric("Routed Chunks", ui_summary["metadata"]["routed_chunk_count"])
            col4.metric("Sections", ui_summary["metadata"]["section_count"])

            st.caption(f"Run directory: {ui_summary['run_dir']}")

            with st.expander("Uploaded files", expanded=False):
                for file_path in saved_files:
                    st.code(file_path)

            st.subheader("Evidence Counts by Category")
            evidence_counts = ui_summary["evidence_counts_by_category"]
            e1, e2, e3, e4, e5 = st.columns(5)
            e1.metric("Activities", evidence_counts.get("activities", 0))
            e2.metric("Outcomes", evidence_counts.get("outcomes", 0))
            e3.metric("Challenges", evidence_counts.get("challenges", 0))
            e4.metric("Lessons", evidence_counts.get("lessons_learned", 0))
            e5.metric("Other", evidence_counts.get("other", 0))

            st.subheader("Generated Sections")
            for section in ui_summary["sections"]:
                render_section_card(section)

            st.subheader("Draft Report")
            st.text_area(
                "Generated draft text",
                value=ui_summary["draft_text"],
                height=350,
            )

            with st.expander("Saved output files", expanded=False):
                st.json(ui_summary["output_paths"])

        except Exception as exc:
            st.exception(exc)
