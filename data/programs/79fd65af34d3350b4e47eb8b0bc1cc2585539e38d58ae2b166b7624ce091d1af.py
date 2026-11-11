def transform(x: str) -> str:
    marker = "(latitude)"
    if marker in x:
        return x.split(marker)[0].strip()
    # fallback: take the first comma-separated part
    return x.split(",")[0].strip()