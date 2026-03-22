"""Write orchestration outputs as JSON-safe run artifacts."""

import json
from pathlib import Path
from typing import Dict, Any

from src.config import RUNS_DIR


def _make_json_safe(value: Any) -> Any:
    """
    Recursively convert values into JSON-safe structures.

    Rules:
    - primitives stay unchanged
    - Path objects become strings
    - dict/list/tuple are traversed recursively
    - objects with to_dict() use that
    - anything else falls back to string representation
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_make_json_safe(v) for v in value]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _make_json_safe(value.to_dict())
        except Exception:
            return str(value)

    return str(value)


def _build_orchestration_payload(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a clean orchestration payload from prototype results.

    Preference order:
    1. ui_summary
    2. metadata
    3. fully JSON-safe fallback of whole result
    """
    payload: Dict[str, Any] = {
        "included_modalities": [],
        "results": {},
    }

    for prototype_name, result in results.items():
        payload["included_modalities"].append(prototype_name)

        if isinstance(result, dict):
            if "ui_summary" in result:
                payload["results"][prototype_name] = _make_json_safe(result["ui_summary"])
            elif "metadata" in result:
                payload["results"][prototype_name] = {
                    "metadata": _make_json_safe(result["metadata"])
                }
            else:
                payload["results"][prototype_name] = _make_json_safe(result)
        else:
            payload["results"][prototype_name] = _make_json_safe(result)

    return payload


def save_orchestration_output(
    run_id: str,
    results: Dict[str, Any],
) -> str:
    """
    Save combined orchestration results.

    Args:
        run_id: Unique run identifier
        results: Outputs collected from all prototypes

    Returns:
        Path to saved orchestration output file
    """
    run_path = Path(RUNS_DIR) / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    output_path = run_path / "orchestration_output.json"
    payload = _build_orchestration_payload(results)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return str(output_path)
