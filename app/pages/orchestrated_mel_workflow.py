from __future__ import annotations

import sys
from pathlib import Path
import json
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from src.orchestration.orchestrator import run_orchestrated_pipeline
from src.orchestration.upload_preparer import prepare_uploaded_inputs
from src.storage import create_run_id


st.set_page_config(page_title="AI-Orchestrated MEL Workflow", layout="wide")

st.title("AI-Orchestrated MEL Workflow")
st.caption("Upload your own data and generate an integrated MEL report.")

# --------------------------------------------------
# Upload Section
# --------------------------------------------------

st.markdown("## Upload Inputs")

form_files = st.file_uploader(
    "Upload attendance form images (Prototype 1 - OCR)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

narrative_files = st.file_uploader(
    "Upload narrative reports (Prototype 2)",
    type=["txt"],
    accept_multiple_files=True,
)

audio_files = st.file_uploader(
    "Upload audio files (Prototype 3)",
    type=["wav", "mp3", "m4a"],
    accept_multiple_files=True,
)

run_id = st.text_input(
    "Run ID",
    value=create_run_id(prefix="upload_run"),
)

run_button = st.button("Run Full MEL Workflow", type="primary", use_container_width=True)

# --------------------------------------------------
# Execution
# --------------------------------------------------

if run_button:
    run_id_clean = run_id.strip()

    if not run_id_clean:
        st.error("Run ID is required.")
        st.stop()

    with st.spinner("Preparing uploaded inputs..."):
        prepared = prepare_uploaded_inputs(
            run_id=run_id_clean,
            form_files=form_files,
            narrative_files=narrative_files,
            audio_files=audio_files,
            clear_existing=True,
        )

    st.success("Files uploaded and prepared.")

    with st.spinner("Running orchestration pipeline..."):
        results = run_orchestrated_pipeline(
            document_input_dir=prepared.get("document_input_dir"),
            narrative_input_dir=prepared.get("narrative_input_dir"),
            audio_input_dir=prepared.get("audio_input_dir"),
            run_id=run_id_clean,
        )

    st.success("MEL workflow completed.")

    # --------------------------------------------------
    # Display Results
    # --------------------------------------------------

    mel_draft = results.get("mel_draft", {})
    attendance_summary = results.get("attendance_summary", {})
    prototype2 = results.get("prototype2", {})
    prototype3 = results.get("prototype3", {})
    report_sections = mel_draft.get("report_sections", [])

    st.markdown("## Integrated MEL Draft")
    if report_sections:
        for section in report_sections:
            with st.container(border=True):
                st.markdown(f"### {section.get('title', 'Section')}")
                st.write(section.get("body", ""))

    st.text_area(
        "Generated draft",
        value=mel_draft.get("mel_draft_text", ""),
        height=400,
    )

    st.markdown("## Attendance Summary")
    if attendance_summary:
        st.json(attendance_summary)
    else:
        st.info("No structured attendance summary was generated.")

    if prototype2:
        st.markdown("## Narrative Summary")
        st.json(prototype2.get("ui_summary", {}))

    if prototype3:
        st.markdown("## Speech Summary")
        st.json(prototype3.get("ui_summary", {}))

    output_path = Path("data/runs") / run_id_clean / "orchestration_output.json"

    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        st.download_button(
            "Download Full Output",
            data=json.dumps(payload, indent=2, ensure_ascii=False),
            file_name="orchestration_output.json",
        )
