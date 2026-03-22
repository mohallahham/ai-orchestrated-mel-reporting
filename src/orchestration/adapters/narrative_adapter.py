"""Convert raw text into a folder structure compatible with Prototype 2."""

from pathlib import Path
from typing import List


def create_narrative_input_from_texts(
    texts: List[str],
    output_dir: str,
) -> str:
    """Create a narrative input directory from raw text inputs."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, text in enumerate(texts, start=1):
        file_path = output_path / f"generated_report_{i:02d}.txt"
        file_path.write_text(text.strip(), encoding="utf-8")

    return str(output_path)
