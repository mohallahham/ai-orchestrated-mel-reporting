def validate_record(record):

    flags = []

    if record.gender_label == "Unknown":
        flags.append("unknown_gender")

    if record.age_value is None:
        flags.append("missing_age")

    if record.age_value is not None:
        if not (10 <= record.age_value <= 35):
            flags.append("age_out_of_range")

    return flags