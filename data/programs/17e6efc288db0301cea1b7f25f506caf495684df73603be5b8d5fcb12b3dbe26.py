import re

def transform(x: str) -> str:
    """
    Extracts the leading number (with commas) from a string like:
    "1,085 inferences, 0.000 CPU in 0.000 seconds (91% CPU, 4254902 Lips)"
    """
    match = re.search(r'^[\d,]+', x.strip())
    return match.group(0) if match else ""