from __future__ import annotations

from typing import Any


def build_ui_summary(
    metadata: dict[str, Any],
    *,
    run_dir: str | None = None,
    output_paths: dict[str, str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "metadata": metadata,
    }

    if run_dir is not None:
        summary["run_dir"] = run_dir

    if output_paths is not None:
        summary["output_paths"] = output_paths

    summary.update(extra)
    return summary


def build_pipeline_result(
    metadata: dict[str, Any],
    *,
    run_dir: str | None = None,
    output_paths: dict[str, str] | None = None,
    artifacts: dict[str, Any] | None = None,
    **ui_summary_extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "metadata": metadata,
        "ui_summary": build_ui_summary(
            metadata,
            run_dir=run_dir,
            output_paths=output_paths,
            **ui_summary_extra,
        ),
    }

    if run_dir is not None:
        result["run_dir"] = run_dir

    if artifacts:
        result.update(artifacts)

    return result
