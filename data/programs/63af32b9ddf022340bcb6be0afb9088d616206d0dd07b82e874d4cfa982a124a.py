def transform(x: str) -> str:
    # Extract the filename from the path
    filename = x.rsplit("/", 1)[-1]
    # Return the extension if present, otherwise empty string
    if "." in filename:
        return filename.rsplit(".", 1)[-1]
    return ""