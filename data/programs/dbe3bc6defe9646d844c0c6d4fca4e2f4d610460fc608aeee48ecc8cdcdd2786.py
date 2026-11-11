def transform(x: str) -> str:
    try:
        domain = x.split("@", 1)[1]
        return domain.split(".", 1)[0]
    except Exception:
        return ""