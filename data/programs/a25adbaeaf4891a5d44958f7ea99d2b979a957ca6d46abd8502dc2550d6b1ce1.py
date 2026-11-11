def transform(x: str) -> str:
    result = []
    for ch in x:
        if ch.isdigit():
            result.append(ch)
        else:
            break
    return "".join(result)