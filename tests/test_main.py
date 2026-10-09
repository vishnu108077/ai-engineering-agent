
from app.main import main
from app.tools.patch import apply_text_patch


def test_application_imports():
    assert main is not None


def test_patch_rejects_text_that_does_not_match(tmp_path):
    target = tmp_path / "utils.py"
    original = "def calculate_total(items):\n    return sum(items)\n"
    target.write_text(original, encoding="utf-8")

    result = apply_text_patch(
        repository=str(tmp_path),
        file_path="utils.py",
        old_text="return sum(items) + 10",
        new_text="return sum(items)",
    )

    assert result["applied"] is False
    assert "Expected exactly one match, found 0" in result["message"]
    assert target.read_text(encoding="utf-8") == original


def test_patch_rejects_path_outside_repository(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()

    outside_file = tmp_path / "outside.py"
    original = "important = True\n"
    outside_file.write_text(original, encoding="utf-8")

    result = apply_text_patch(
        repository=str(repository),
        file_path="../outside.py",
        old_text="important = True",
        new_text="important = False",
    )

    assert result["applied"] is False
    assert "outside the authorized repository" in result["message"]
    assert outside_file.read_text(encoding="utf-8") == original


def test_patch_applies_exact_replacement(tmp_path):
    target = tmp_path / "utils.py"
    original = "def calculate_total(items):\n    return sum(items) + 10\n"
    expected = "def calculate_total(items):\n    return sum(items)\n"
    target.write_text(original, encoding="utf-8")

    result = apply_text_patch(
        repository=str(tmp_path),
        file_path="utils.py",
        old_text="return sum(items) + 10",
        new_text="return sum(items)",
        dry_run=False,
    )

    assert result["applied"] is True
    assert target.read_text(encoding="utf-8") == expected
