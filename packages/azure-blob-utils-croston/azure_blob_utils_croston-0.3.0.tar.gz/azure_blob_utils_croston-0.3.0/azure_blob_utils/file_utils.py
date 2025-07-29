import os
from pathlib import Path

def file_exists(path: str) -> bool:
    """Check if a file exists at the given path."""
    return Path(path).is_file()

def get_file_size(path: str) -> int:
    """Return the size of the file in bytes."""
    return Path(path).stat().st_size if file_exists(path) else 0

def ensure_directory(path: str):
    """Create the directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def delete_file(path: str):
    """Delete a file if it exists."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
