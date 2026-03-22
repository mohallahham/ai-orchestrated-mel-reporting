from pathlib import Path

from src.prototype1.vision.ollama_vision import call_vision_model


FAST_MODEL = "moondream"
STRONG_MODEL = "llama3.2-vision"


def is_suspicious_result(result):
    """
    Decide whether the fast model output is unreliable.
    """

    age = result.get("age")
    gender = result.get("gender")

    if age is None:
        return True

    # suspicious ages often hallucinated
    if age in [35, 36, 37]:
        return True

    if gender not in ["Male", "Female"]:
        return True

    return False


def extract_with_orchestration(row_path: Path, debug=False):

    # First pass: fast model
    fast_result = call_vision_model(row_path, model=FAST_MODEL)

    if debug:
        print("Fast model result:", fast_result)

    if not is_suspicious_result(fast_result):
        return fast_result, "fast"

    # Escalate to stronger model
    strong_result = call_vision_model(row_path, model=STRONG_MODEL)

    if debug:
        print("Escalated result:", strong_result)

    return strong_result, "strong"