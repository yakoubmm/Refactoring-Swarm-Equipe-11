 
from pathlib import Path

# Absolute path to the sandbox directory
SANDBOX_ROOT = Path("sandbox").resolve()


def resolve_and_validate_path(user_path: str) -> Path:
    """
    Resolve a path and ensure it is inside the sandbox directory.
    Raises PermissionError if the path escapes the sandbox.
    """
    resolved_path = Path(user_path).resolve()

    if not resolved_path.is_relative_to(SANDBOX_ROOT):
        raise PermissionError(
            f"Access denied: '{resolved_path}' is outside the sandbox"
        )

    return resolved_path


def read_file(path: str) -> str:
    """
    Read and return the content of a file inside the sandbox.
    """
    safe_path = resolve_and_validate_path(path)

    if not safe_path.exists():
        raise FileNotFoundError(f"File not found: {safe_path}")

    if not safe_path.is_file():
        raise IsADirectoryError(f"Not a file: {safe_path}")

    return safe_path.read_text(encoding="utf-8")
