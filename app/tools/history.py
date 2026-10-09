
import json
from pathlib import Path


def save_repair_history(
    record: dict,
    history_file: str = "reports/repair_history.json",
) -> None:
    """Append one repair record to a JSON history file."""
    path = Path(history_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        history = json.loads(path.read_text(encoding="utf-8"))
    else:
        history = []

    history.append(record)

    path.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8",
    )


def load_repair_history(
    history_file: str = "reports/repair_history.json",
) -> list[dict]:
    """Load saved repair records, returning an empty list if none exist."""
    path = Path(history_file)

    if not path.exists():
        return []

    return json.loads(path.read_text(encoding="utf-8"))

