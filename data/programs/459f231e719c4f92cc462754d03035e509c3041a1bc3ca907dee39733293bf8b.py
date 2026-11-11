def transform(x: str) -> str:
    for token in x.split():
        # Skip tokens that are purely numeric (house numbers)
        if token.isdigit():
            continue
        # Return the first non-numeric token, stripped of trailing commas
        return token.rstrip(',') 
    return ""