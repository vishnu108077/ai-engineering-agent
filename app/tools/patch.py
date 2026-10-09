
from pathlib import Path


def apply_text_patch(
    repository: str,
    file_path: str,
    old_text: str,
    new_text: str,
    dry_run: bool = True,
) -> dict:
    """Preview or apply an exact text replacement inside a repository."""
    root = Path(repository).resolve()
    path = (root / file_path).resolve()

    if not path.is_relative_to(root):
        return {
            "applied": False,
            "message": "Rejected: target is outside the authorized repository.",
        }

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Not a file: {path}")

    content = path.read_text(encoding="utf-8")
    occurrences = content.count(old_text)

    if occurrences != 1:
        return {
            "applied": False,
            "message": (
                f"Expected exactly one match, found {occurrences}. "
                "File was not changed."
            ),
        }

    updated_content = content.replace(old_text, new_text, 1)

    if dry_run:
        return {
            "applied": False,
            "preview": updated_content,
            "message": "Dry run: preview generated; file was not changed.",
        }

    path.write_text(updated_content, encoding="utf-8")

    return {
        "applied": True,
        "message": f"Patch applied to {file_path}",
    }
