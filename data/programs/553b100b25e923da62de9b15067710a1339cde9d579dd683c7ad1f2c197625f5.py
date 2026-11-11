def transform(x: str) -> str:
    # Find the first space which separates the day from the month
    first_space = x.find(' ')
    if first_space == -1:
        return ''
    # Find the comma that follows the month name
    comma = x.find(',', first_space)
    if comma == -1:
        return ''
    # Extract the month name and strip any surrounding whitespace
    return x[first_space + 1:comma].strip()