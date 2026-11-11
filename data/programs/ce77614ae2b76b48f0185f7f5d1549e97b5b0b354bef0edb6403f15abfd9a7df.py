def transform(x: str) -> str:
    # Extract the first token (up to first whitespace) which contains the phone number
    phone = x.split()[0]
    # Find the first hyphen and return everything after it
    i = phone.find('-')
    return phone[i + 1:] if i != -1 else ''