import re


ARABIC_TO_WESTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize(text: str):

    if not text:
        return ""

    return (
        text.replace(" ", "")
        .replace("ـ", "")
        .replace("|", "")
        .replace("`", "")
        .replace("’", "")
        .replace("'", "")
    )


def classify_gender(raw_text: str):

    t = normalize(raw_text)

    if any(x in t for x in ["أنثى", "انثى", "أن", "ان", "ث"]):
        return "Female"

    if ("ذ" in t) or ("كر" in t) or ("دك" in t) or t.startswith("د"):
        return "Male"

    if ("ل" in t and "ر" in t):
        return "Male"

    return "Unknown"


def extract_age(raw_text: str):

    t = normalize(raw_text).translate(ARABIC_TO_WESTERN)

    digits = re.findall(r"\d", t)

    if len(digits) >= 2:

        candidate = int(digits[0] + digits[1])

        if 10 <= candidate <= 35:
            return candidate

        candidate2 = int(digits[1] + digits[0])

        if 10 <= candidate2 <= 35:
            return candidate2

    return None