import re

def transform(x: str) -> str:
    # Split on commas and take the last segment (which contains the postcode)
    segment = x.split(",")[-1].strip()
    tokens = segment.split()
    # If the second‑last token looks like part of a UK postcode (contains a digit),
    # treat the last two tokens as the postcode and everything before as the city.
    if len(tokens) >= 2 and any(ch.isdigit() for ch in tokens[-2]):
        city_tokens = tokens[:-2]
    else:
        # Fallback: assume the whole segment is the city name
        city_tokens = tokens
    return " ".join(city_tokens).strip()
