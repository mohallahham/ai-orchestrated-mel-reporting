# AI-Orchestrated MEL Reporting

This repository contains a final-year project exploring how multiple pre-trained AI models can be orchestrated to support Monitoring, Evaluation, and Learning (MEL) workflows in NGO contexts.

The system combines three main prototype pipelines:

- `Prototype 1`: attendance-form extraction from sign-in sheets using OCR and local multimodal vision
- `Prototype 2`: grounded narrative analysis and evidence-based draft generation from text reports
- `Prototype 3`: speech-to-text transcription for audio evidence

These components are coordinated through an orchestration layer that produces an integrated MEL-style draft report through a Streamlit interface.

## Repository Structure

- `app/` Streamlit application pages and shared UI helpers
- `src/` core prototype pipelines and orchestration code
- `tests/` automated contract-based regression tests
- `data/inputs/` small public sample inputs for demonstration
- `data/ground_truth/` manually verified reference files used in Prototype 1 evaluation


## Environment

This project was developed and tested with `Python 3.10`.

## Installation

Install the Python dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

## Additional Requirement

This project also requires [Ollama](https://ollama.com/) to be installed locally in order to run the local multimodal models used in this project.

After installing Ollama, pull the required models:

```bash
ollama pull moondream
ollama pull llama3.2-vision
```

## Running the App

From the repository root, run:

```bash
python -m streamlit run app/streamlit_app.py
```

## Running the Tests

The repository includes a lightweight regression suite that checks pipeline and orchestration result contracts:

```bash
python -m pytest -v tests/test_pipeline_contracts.py
```

## Notes

This repository intentionally excludes large generated run artifacts, temporary uploads, and development leftovers. It keeps only:

- the core source code
- the user-facing Streamlit app
- a small sample dataset
- the automated regression test suite
