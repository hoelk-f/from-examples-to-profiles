import re

def transform(x: str) -> str:
    # Split on the first comma
    parts = x.split(',', 1)
    if len(parts) < 2:
        return ""
    after_comma = parts[1].strip()
    # Tokens separated by whitespace
    tokens = after_comma.split()
    city_parts = []
    for token in tokens:
        # Stop when token is a number (all digits)
        if token.isdigit():
            break
        city_parts.append(token)
    return " ".join(city_parts)