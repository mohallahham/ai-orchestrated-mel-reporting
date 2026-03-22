from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from app.shared import (
    list_run_images,
    reset_directory,
    save_uploaded_files,
)

from src.prototype1.pipeline import (
    run_extraction_pipeline,
)
from src.prototype1.baseline_ocr.pipeline import run_baseline_ocr_pipeline


APP_INPUT_DIR = Path("data/inputs/forms_app")


def display_uploaded_image_previews(saved_files: list[str]) -> None:
    if not saved_files:
        return

    st.subheader("Uploaded Image Preview")

    cols = st.columns(min(2, len(saved_files)))
    for idx, file_path in enumerate(saved_files):
        with cols[idx % len(cols)]:
            st.image(file_path, caption=Path(file_path).name, use_container_width=True)


def display_run_images(run_path: str | None) -> None:
    image_paths = list_run_images(run_path)

    if not image_paths:
        st.write("No saved debug or crop images found for this run.")
        return

    st.write(f"Found {len(image_paths)} saved image artefacts.")

    cols = st.columns(2)
    for idx, image_path in enumerate(image_paths):
        with cols[idx % 2]:
            st.image(str(image_path), caption=image_path.name, use_container_width=True)


st.set_page_config(page_title="Prototype 1 - Document Extraction", layout="wide")

st.title("Prototype 1: Attendance Form Extraction")
st.write(
    """
Upload scanned or photographed attendance forms to extract structured participant records.
This page supports OCR-based full-form extraction and cropped-input OCR.
"""
)

with st.expander("What this page does", expanded=False):
    st.markdown(
        """
- Loads uploaded attendance form images  
- Supports OCR extraction modes  
- Extracts age and gender fields with OCR  
- Applies validation checks  
- Saves structured outputs and debug artefacts to run folders  
- Displays uploaded images and saved analysis artefacts where available  
"""
    )

mode = st.selectbox(
    "Select extraction mode",
    [
        "Full Form (Auto-detect + Crop)",
        "Cropped Input (Baseline OCR)",
    ],
)

uploaded_files = st.file_uploader(
    "Upload form images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

run_button = st.button("Run Extraction Pipeline", type="primary")

if uploaded_files:
    APP_INPUT_DIR.mkdir(parents=True, exist_ok=True)

if run_button:
    if not uploaded_files:
        st.error("Please upload at least one image.")
    else:
        try:
            reset_directory(APP_INPUT_DIR)
            saved_files = save_uploaded_files(uploaded_files, APP_INPUT_DIR)

            display_uploaded_image_previews(saved_files)

            runs = []

            with st.spinner("Running extraction pipeline..."):
                for file_path in saved_files:
                    if mode == "Full Form (Auto-detect + Crop)":
                        result = run_extraction_pipeline(file_path)
                    else:
                        result = run_baseline_ocr_pipeline(file_path)

                    runs.append(
                        {
                            "image_name": Path(file_path).name,
                            "image_path": file_path,
                            "record_count": len(result["records"]),
                            "summary": result["summary"],
                            "run_path": result["run_path"],
                        }
                    )

            total_records = sum(run["record_count"] for run in runs)
            successful_forms = len([run for run in runs if run["run_path"]])

            ui_summary = {
                "metadata": {
                    "form_count": len(runs),
                    "successful_forms": successful_forms,
                    "total_records": total_records,
                    "mode": mode,
                    "output_files": [
                        "attendance_records.csv",
                        "attendance_records.json",
                        "attendance_summary.json",
                        "debug images",
                        "crops (where available)",
                    ],
                },
                "runs": runs,
            }

            st.success("Extraction pipeline completed.")

            st.subheader("Run Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Forms Uploaded", ui_summary["metadata"]["form_count"])
            col2.metric("Successful Runs", ui_summary["metadata"]["successful_forms"])
            col3.metric("Total Extracted Records", ui_summary["metadata"]["total_records"])

            st.caption(f"Selected mode: {ui_summary['metadata']['mode']}")

            with st.expander("Uploaded files", expanded=False):
                for file_path in saved_files:
                    st.code(file_path)

            st.subheader("Per-Form Results")
            for run in ui_summary["runs"]:
                with st.container(border=True):
                    st.markdown(f"### {run['image_name']}")

                    st.image(
                        run["image_path"],
                        caption=f"Uploaded input: {run['image_name']}",
                        use_container_width=True,
                    )

                    col_a, col_b = st.columns(2)
                    col_a.metric("Extracted Records", run["record_count"])
                    col_b.caption(f"Run folder: {run['run_path'] or 'No run folder created'}")

                    with st.expander("Show summary", expanded=False):
                        st.json(run["summary"])

                    with st.expander("Show saved analysis images", expanded=False):
                        display_run_images(run["run_path"])

            with st.expander("Expected output files per successful run", expanded=False):
                st.json(ui_summary["metadata"]["output_files"])

        except Exception as exc:
            st.exception(exc)
