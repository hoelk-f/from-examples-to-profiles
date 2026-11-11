import re

def transform(x: str) -> str:
    """
    Extract the longitude value from a string of the form:
    "<latitude>(latitude), <longitude>(longitude)"
    """
    match = re.search(r'([+-]?\d+(?:\.\d+)?)\s*\(longitude\)', x)
    return match.group(1) if match else ""