def transform(x: str) -> str:
    """
    Extracts the substring after the first '=' character and strips surrounding whitespace.
    If no '=' is present, returns the input string stripped of leading/trailing whitespace.
    """
    parts = x.split('=', 1)
    return parts[1].strip() if len(parts) == 2 else x.strip()