from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}


def list_files(directory: str) -> list[str]:
    """Return relevant files inside a directory recursively."""
    root = Path(directory)

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        if path.suffix == ".pyc":
            continue

        files.append(str(path.relative_to(root)))

    return files


def read_file(file_path: str) -> str:
    """Read and return the contents of a text file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise IsADirectoryError(f"Not a file: {file_path}")

    return path.read_text(encoding="utf-8")
