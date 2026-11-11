def transform(x: str) -> str:
    idx_slash_n = x.rfind("/n")
    idx_newline = x.rfind("\n")
    idx = max(idx_slash_n, idx_newline)
    if idx != -1:
        return x[idx + 2 :]
    return x