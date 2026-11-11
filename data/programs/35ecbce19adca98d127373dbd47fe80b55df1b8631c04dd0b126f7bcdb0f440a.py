def transform(x: str) -> str:
    # Find the separator that marks the end of the desired part
    hyphen_idx = x.find(' -')
    if hyphen_idx == -1:
        hyphen_idx = x.find('-')
    # Determine where the meaningful content starts (after a leading "NN. ")
    start_idx = 0
    dot_space_idx = x.find('. ')
    if dot_space_idx != -1:
        start_idx = dot_space_idx + 2
    # Extract and clean the segment
    segment = x[start_idx:hyphen_idx] if hyphen_idx != -1 else x[start_idx:]
    return segment.strip()