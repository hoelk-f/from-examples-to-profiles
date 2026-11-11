def transform(x: str) -> str:
    # Split the string into words, take the last non‑empty one,
    # and strip surrounding punctuation.
    for word in reversed(x.split()):
        if word:
            # Remove leading/trailing punctuation characters
            return word.strip(".,!?:;\"'`()[]{}")
    return ""