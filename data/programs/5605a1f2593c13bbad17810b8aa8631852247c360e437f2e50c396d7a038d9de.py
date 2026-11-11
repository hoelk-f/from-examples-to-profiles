def transform(x: str) -> str:
    # Get the last whitespace-separated token (the filename)
    filename = x.rsplit(None, 1)[-1]
    # Return the substring after the last dot, or empty string if none
    return filename.rsplit(".", 1)[-1] if "." in filename else ""