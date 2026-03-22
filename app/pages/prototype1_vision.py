from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from app.shared import list_run_images, reset_directory, save_uploaded_files

from src.prototype1.vision.pipeline import VisionExtractionEngine


APP_INPUT_DIR = Path("data/inputs/vision_app")


def display_uploaded_images(files: list[str]) -> None:
    st.subheader("Uploaded Image Preview")
    cols = st.columns(min(2, len(files)))
    for i, f in enumerate(files):
        with cols[i % len(cols)]:
            st.image(f, caption=Path(f).name, use_container_width=True)


def display_run_images(run_path: str | None) -> None:
    image_paths = list_run_images(run_path)
    if not image_paths:
        st.write("No debug images found.")
        return

    st.write(f"{len(image_paths)} saved images")

    cols = st.columns(2)
    for i, p in enumerate(sorted(image_paths)):
        with cols[i % 2]:
            st.image(str(p), caption=p.name, use_container_width=True)


st.set_page_config(page_title="Prototype 1 - Vision Extraction", layout="wide")

st.title("Prototype 1: AI Vision Extraction")
st.write(
    """
This workflow uses a vision-language model to extract structured data from attendance forms.

Unlike OCR, this approach:
- understands layout implicitly
- handles handwriting better
- uses model reasoning instead of character recognition
"""
)

with st.expander("Pipeline Overview", expanded=False):
    st.markdown(
        """
1. Detect table region from full form  
2. Crop age/gender fields  
3. Detect rows  
4. Extract each row using vision model  
5. Apply validation  
6. Save structured outputs + debug artefacts  
"""
    )

st.subheader("Settings")

col1, col2 = st.columns(2)

extraction_mode = col1.radio(
    "Vision extraction mode",
    ["Hybrid (Fast → Strong fallback)", "Fast only"],
    index=0,
)

max_rows = col2.number_input(
    "Limit rows (for testing)",
    min_value=1,
    max_value=50,
    value=10,
)

uploaded_files = st.file_uploader(
    "Upload attendance forms",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

run_button = st.button("Run Vision Extraction", type="primary")

if run_button:
    if not uploaded_files:
        st.error("Please upload at least one image.")
    else:
        try:
            reset_directory(APP_INPUT_DIR)
            saved_files = save_uploaded_files(uploaded_files, APP_INPUT_DIR)

            display_uploaded_images(saved_files)

            engine = VisionExtractionEngine()
            runs = []

            fast_mode = extraction_mode == "Fast only"

            with st.spinner("Running vision pipeline..."):
                for file_path in saved_files:
                    result = engine.extract_rows(
                        image_path=file_path,
                        fast_mode=fast_mode,
                        max_rows=max_rows,
                        debug=False,
                        save_outputs=True,
                    )

                    runs.append(
                        {
                            "image": file_path,
                            "records": result["records"],
                            "summary": result["summary"],
                            "run_path": result["run_path"],
                        }
                    )

            st.success("Vision extraction completed.")

            total_records = sum(len(r["records"]) for r in runs)

            st.subheader("Run Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Images processed", len(runs))
            c2.metric("Total extracted records", total_records)
            c3.metric("Mode", extraction_mode)

            st.subheader("Results")

            for run in runs:
                with st.container(border=True):
                    st.markdown(f"### {Path(run['image']).name}")
                    st.image(run["image"], use_container_width=True)
                    st.metric("Extracted rows", len(run["records"]))

                    with st.expander("Structured Output"):
                        st.json([r.to_dict() for r in run["records"]])

                    with st.expander("Summary"):
                        st.json(run["summary"])

                    with st.expander("Debug Images"):
                        display_run_images(run["run_path"])

        except Exception as exc:
            st.exception(exc)
