import os
import re


def secure_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and remove potentially unsafe
    characters.

    This function:
    1. Extracts only the basename of the file (handling both Windows and POSIX paths).
    2. Removes any characters that are not alphanumeric, dot, hyphen, or underscore.
    3. Prevents empty filenames.
    """
    if not filename:
        return "unnamed_file"

    # Handle Windows paths by replacing backslashes with forward slashes
    filename = filename.replace("\\", "/")

    # Get just the basename
    filename = os.path.basename(filename)

    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)

    # Remove leading dots to prevent hidden files
    filename = filename.lstrip('.')

    # Ensure it's not empty after cleaning
    if not filename:
        return "unnamed_file"

    return filename
