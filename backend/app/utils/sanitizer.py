import re
import os

def sanitize_text(text: str) -> str:
    """
    Sanitizes plain text to prevent XSS and HTML injection.
    Escapes HTML tag delimiters and removes javascript: prefixes.
    """
    if not isinstance(text, str):
        return text
    # Escape simple HTML tags
    escaped = text.replace("<", "&lt;").replace(">", "&gt;")
    # Strip potentially dangerous Javascript injection strings
    escaped = re.sub(r"(?i)javascript:", "", escaped)
    return escaped

import urllib.parse

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filenames to prevent path traversal attacks.
    Removes directory path components and unsafe chars.
    """
    if not isinstance(filename, str):
        return filename
    # Remove null bytes first
    filename = filename.replace("\x00", "")
    # URL decode to handle encoded traversal patterns (e.g., %2f)
    filename = urllib.parse.unquote(filename)
    # Normalize Windows backslashes to Unix forward slashes
    normalized = filename.replace("\\", "/")
    # Extract only the base name (final component after last slash)
    base = normalized.split("/")[-1]
    # Remove any character that is not alphanumeric, a dot, space, dash, or underscore
    cleaned = re.sub(r"[^a-zA-Z0-9._ -]", "", base)
    # Strip leading dots or multiple dots
    cleaned = re.sub(r"\.+", ".", cleaned)
    if cleaned.startswith("."):
        cleaned = cleaned[1:]
    return cleaned or "file"

def sanitize_search_query(query: str) -> str:
    """
    Sanitizes search queries.
    """
    return sanitize_text(query)
