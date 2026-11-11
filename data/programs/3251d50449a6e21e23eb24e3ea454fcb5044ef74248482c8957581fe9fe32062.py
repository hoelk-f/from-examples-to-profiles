def transform(x: str) -> str:
    """
    Extract the file extension from a string that ends with a filename.
    The extension is the substring after the last '.' in the filename.
    If no '.' is present, returns an empty string.
    """
    # Get the last whitespace-separated token (assumed to be the filename)
    filename = x.strip().split()[-1]
    # Return the part after the final dot, if any
    if "." in filename:
        return filename.rsplit(".", 1)[-1]
    return ""