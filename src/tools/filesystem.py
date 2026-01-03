 
from pathlib import Path

# Absolute path to the sandbox directory
SANDBOX_ROOT = Path("sandbox").resolve()

# Function to ensure the agents don't access anything outside sandbox folder 
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

# Function to list all python files in the sandbox folder
def list_python_files(directory: str) -> list[str]:
    """
    Recursively list all Python (.py) files inside a sandbox directory.

    Args:
        directory (str): Path to a directory inside the sandbox

    Returns:
        list[str]: List of file paths as strings
    """
    safe_dir = resolve_and_validate_path(directory) # call the security function

    if not safe_dir.exists():
        raise FileNotFoundError(f"Directory not found: {safe_dir}")

    if not safe_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {safe_dir}")

    python_files = []

    for path in safe_dir.rglob("*.py"):
        if path.is_file():
            python_files.append(str(path))

    return python_files


# Function to read a python file and return it's content as a string
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
