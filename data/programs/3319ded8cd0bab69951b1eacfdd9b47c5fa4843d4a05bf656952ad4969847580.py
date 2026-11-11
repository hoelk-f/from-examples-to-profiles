def transform(x: str) -> str:
    # Split off the trailing part after a space (e.g., " x4202")
    phone_part = x.split(" ", 1)[0]
    # Split the phone number on hyphens and drop the first segment
    segments = phone_part.split("-")
    return "-".join(segments[1:])