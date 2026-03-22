from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def reset_directory(folder: Path) -> None:
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)


def save_uploaded_files(uploaded_files: Iterable, target_dir: Path) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[str] = []

    for uploaded_file in uploaded_files:
        file_path = target_dir / uploaded_file.name
        file_path.write_bytes(uploaded_file.getbuffer())
        saved_files.append(str(file_path))

    return saved_files


def list_run_images(run_path: str | None) -> list[Path]:
    if not run_path:
        return []

    run_dir = Path(run_path)
    if not run_dir.exists():
        return []

    image_paths = []
    for path in run_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            image_paths.append(path)

    return sorted(image_paths)
