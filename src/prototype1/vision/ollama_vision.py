import base64
import json
from pathlib import Path

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT_SECONDS = 180

ROW_SCHEMA = {
    "type": "object",
    "properties": {
        "gender": {
            "type": ["string", "null"],
            "enum": ["Male", "Female", "Unknown", None],
        },
        "age": {
            "type": ["integer", "null"],
            "minimum": 10,
            "maximum": 99,
        },
        "notes": {"type": "string"},
    },
    "required": ["gender", "age", "notes"],
}

VISION_PROMPT = """Extract handwritten attendance data from this single row image.

Return JSON only.

Fields:
- gender: Male, Female, or Unknown
- age: integer or null
- notes: short explanation if uncertain

Rules:
- be conservative
- do not guess
- if unclear, return Unknown or null
- keep notes very short

Arabic hints:
- ذكر = Male
- أنثى = Female
"""


def _encode_image_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _timeout_result(model: str) -> dict:
    return {
        "gender": "Unknown",
        "age": None,
        "notes": f"timeout:{model}",
    }


def _request_error_result(model: str, message: str) -> dict:
    return {
        "gender": "Unknown",
        "age": None,
        "notes": f"request_error:{model}:{message[:80]}",
    }


def call_vision_model(image_path: Path, model: str) -> dict:
    image_b64 = _encode_image_base64(image_path)

    payload = {
        "model": model,
        "prompt": VISION_PROMPT,
        "images": [image_b64],
        "format": ROW_SCHEMA,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 80,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
    except requests.exceptions.ReadTimeout:
        return _timeout_result(model)
    except requests.exceptions.RequestException as exc:
        return _request_error_result(model, str(exc))

    if not response.ok:
        return {
            "gender": "Unknown",
            "age": None,
            "notes": f"ollama_error:{model}:{response.status_code}",
        }

    raw = response.json().get("response", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "gender": "Unknown",
            "age": None,
            "notes": f"non_json:{model}:{raw[:120]}",
        }
