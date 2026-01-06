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


def list_python_files(directory: str) -> list[str]:
    """
    Recursively list all Python (.py) files inside a sandbox directory.
    """
    safe_dir = resolve_and_validate_path(directory)

    if not safe_dir.exists():
        raise FileNotFoundError(f"Directory not found: {safe_dir}")

    if not safe_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {safe_dir}")

    return [str(path) for path in safe_dir.rglob("*.py") if path.is_file()]


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


def write_file(path: str, content: str) -> None:
    """
    Write content to a file inside the sandbox.
    - Creates the file if it does not exist
    - Overwrites the file if it already exists
    """
    safe_path = resolve_and_validate_path(path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
