def transform(x: str) -> str:
    marker = "Model:"
    if marker in x:
        # Split on the marker and take the part after it
        _, after = x.split(marker, 1)
        return after.strip()
    # Fallback: return the last word after any colon
    if ":" in x:
        return x.rsplit(":", 1)[-1].strip()
    return x.strip()