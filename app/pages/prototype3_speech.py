from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from app.shared import reset_directory, save_uploaded_files

from src.prototype3.pipeline import run_prototype3_pipeline


APP_INPUT_DIR = Path("data/inputs/audio_app")


st.set_page_config(page_title="Prototype 3 - Speech-to-Text", layout="wide")

st.title("Prototype 3: Speech-to-Text")
st.write(
    """
Upload audio recordings to generate transcripts.
This workflow converts spoken content into structured text outputs for later MEL use.
"""
)

with st.expander("What this page does", expanded=False):
    st.markdown(
        """
- Loads uploaded audio files  
- Runs local speech-to-text transcription  
- Produces transcript text and structured JSON outputs  
- Saves run artefacts for inspection and reuse  
"""
    )

uploaded_files = st.file_uploader(
    "Upload audio files",
    type=["mp3", "wav", "m4a"],
    accept_multiple_files=True,
)

run_button = st.button("Run Transcription Pipeline", type="primary")

if run_button:
    if not uploaded_files:
        st.error("Please upload at least one audio file.")
    else:
        try:
            reset_directory(APP_INPUT_DIR)
            saved_files = save_uploaded_files(uploaded_files, APP_INPUT_DIR)

            with st.spinner("Running transcription pipeline..."):
                result = run_prototype3_pipeline(input_dir=APP_INPUT_DIR)
                ui = result["ui_summary"]

            st.success("Transcription completed.")

            st.subheader("Run Summary")
            col1, col2 = st.columns(2)
            col1.metric("Audio Files Processed", ui["document_count"])
            col2.caption(f"Run directory: {ui['run_dir']}")

            with st.expander("Uploaded files", expanded=False):
                for f in saved_files:
                    st.code(f)

            st.subheader("Transcript Preview")
            with st.container(border=True):
                st.write(ui["transcript_preview"] or "No transcript text available.")

            with st.expander("Saved output files", expanded=False):
                st.json(ui["output_paths"])

        except Exception as exc:
            st.exception(exc)
