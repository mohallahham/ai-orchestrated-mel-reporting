import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)

if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

st.set_page_config(
    page_title="AI-Orchestrated MEL Reporting System",
    layout="wide",
)

st.title("AI-Orchestrated MEL Reporting System")

st.markdown(
    """
This application demonstrates a modular AI system designed to support Monitoring, Evaluation, and Learning (MEL) workflows.

The system integrates three AI-powered pipelines:

- **Prototype 1 — Document Extraction**  
  Extract structured participant data from attendance forms.

- **Prototype 2 — Narrative Analysis**  
  Organize qualitative reports into structured evidence and generate draft report sections.

- **Prototype 3 — Speech-to-Text**  
  Convert audio recordings into transcripts for further analysis.

---

### How to use the system

1. Select a prototype from the sidebar
2. Upload your input data (image, text, or audio)
3. Run the pipeline
4. Review outputs and saved run artefacts

---

### Key Features

- Modular backend architecture
- Reproducible run outputs
- Human-in-the-loop design
- Transparent intermediate artefacts
- Multi-modal data processing (image, text, audio)

---

This system is a research-oriented implementation of AI-assisted MEL reporting workflows.
"""
)

st.divider()

st.subheader("System Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Prototype 1")
    st.write("Form → Structured Data")
    st.write("OCR, cropping, validation")

with col2:
    st.markdown("### Prototype 2")
    st.write("Reports → Evidence → Draft")
    st.write("Chunking, routing, synthesis")

with col3:
    st.markdown("### Prototype 3")
    st.write("Audio → Transcript")
    st.write("Speech-to-text processing")

st.divider()

st.info(
    "Use the sidebar to navigate between prototypes and explore the system."
)
