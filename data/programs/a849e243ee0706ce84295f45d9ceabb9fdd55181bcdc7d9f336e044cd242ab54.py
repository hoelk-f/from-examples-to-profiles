def transform(x: str) -> str:
    import os
    base = os.path.basename(x)
    if '.' in base:
        return base.rsplit('.', 1)[1]
    return ''