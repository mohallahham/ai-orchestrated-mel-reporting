from datetime import datetime
from pathlib import Path
import json

from src.config import RUNS_DIR


def timestamp_string() -> str:
    """Return a compact timestamp string for filenames and run IDs."""
    return datetime.now().strftime("%Y_%m_%d_%H%M%S")


def ensure_directory(path: Path) -> Path:
    """Create directory if it does not exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: dict, path: Path, encoding: str = "utf-8") -> None:
    """Save a dictionary as formatted JSON."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path, encoding: str = "utf-8") -> dict:
    """Load JSON file and return as dict."""
    with open(path, "r", encoding=encoding) as f:
        return json.load(f)


# ---------------------------------------------------------
# Run directory helpers
# ---------------------------------------------------------


def make_run_dir(prefix: str = "run") -> str:
    """
    Create a new run directory inside data/runs.

    Example:
        data/runs/prototype2_run_2026_03_17_142233

    Returns
    -------
    str
        Path to the created run directory
    """

    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    run_dir = RUNS_DIR / f"{prefix}_{timestamp}"

    run_dir.mkdir(parents=True, exist_ok=True)

    return str(run_dir)
