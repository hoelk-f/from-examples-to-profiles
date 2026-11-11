def transform(x: str) -> str:
    """
    Extracts the header name from a C #include directive.
    Example: "#include <stdio.h>" -> "stdio"
    """
    start = x.find('<')
    end = x.find('>', start + 1)
    if start == -1 or end == -1:
        return ""
    header = x[start + 1:end]
    # Remove extension if present (e.g., ".h")
    return header.split('.')[0]