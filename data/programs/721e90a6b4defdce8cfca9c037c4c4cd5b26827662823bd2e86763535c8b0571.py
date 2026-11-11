import re

def transform(x: str) -> str:
    match = re.search(
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
        x,
        re.IGNORECASE,
    )
    return match.group(0) if match else ""