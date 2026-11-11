def transform(x: str) -> str:
    # Get the last whitespace-separated token (the filename)
    filename = x.strip().split()[-1]
    # Find the last dot in the filename
    idx = filename.rfind('.')
    # Return the extension if a dot is found, otherwise empty string
    return filename[idx + 1:] if idx != -1 else ""