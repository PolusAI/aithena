"""Local utils module to replace polus.aithena.common.utils dependency."""

import os
from pathlib import Path


def init_dir(path: Path) -> Path:
    """Initialize a directory, creating it if it doesn't exist.
    
    Args:
        path: Path to the directory.
    
    Returns:
        The Path object for the directory.
    
    Raises:
        PermissionError: If the directory cannot be created.
    """
    # Resolve to absolute path
    path = path.resolve()
    
    # Create directory if it doesn't exist
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(f"Cannot create directory {path}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to initialize directory {path}: {e}") from e
    
    # Verify it's actually a directory
    if not path.is_dir():
        raise ValueError(f"Path exists but is not a directory: {path}")
    
    return path


def ensure_file_dir(file_path: Path) -> Path:
    """Ensure the parent directory of a file exists.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        The Path object for the file.
    """
    parent_dir = file_path.parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    return file_path


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not set.
    
    Returns:
        Boolean value.
    """
    value = os.getenv(key, "").lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "y", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not set.
    
    Returns:
        Integer value.
    """
    value = os.getenv(key, "")
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def format_bytes(size: int) -> str:
    """Format bytes into human-readable string.
    
    Args:
        size: Size in bytes.
    
    Returns:
        Formatted string (e.g., "1.5 GB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def truncate_string(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.
    
    Args:
        text: String to truncate.
        max_length: Maximum length.
        suffix: Suffix to add when truncated.
    
    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
