from pathlib import Path
from datetime import datetime
from src.config import RUNS_DIR
from src.utils import ensure_directory, save_json


def create_run_id(prefix: str = "run") -> str:
    """Create a unique run ID."""
    now = datetime.now()
    return f"{prefix}_{now.strftime('%Y_%m_%d_%H%M%S')}"


def create_run_folder(run_id: str) -> Path:
    """Create and return a run folder path."""
    run_path = RUNS_DIR / run_id
    ensure_directory(run_path)
    return run_path


def save_run_metadata(run_path: Path, metadata: dict) -> Path:
    """Save metadata.json in a run folder."""
    metadata_path = run_path / "metadata.json"
    save_json(metadata, metadata_path)
    return metadata_path