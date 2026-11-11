def transform(x: str) -> str:
    # Extract the content inside the first pair of parentheses
    start = x.find('(')
    end = x.find(')', start + 1)
    if start != -1 and end != -1:
        return x[start + 1:end].strip()
    # Fallback: return the original string if no parentheses are found
    return x.strip()