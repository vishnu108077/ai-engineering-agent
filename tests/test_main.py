from app.agent import Agent
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

  


def test_repair_rejects_patches_to_test_files(tmp_path, monkeypatch):
    from app import agent as agent_module

    repository = tmp_path
    test_file = repository / "tests" / "test_app.py"
    test_file.parent.mkdir()
    original = "def test_example():\n    assert 1 == 2\n"
    test_file.write_text(original, encoding="utf-8")

    instance = Agent(str(repository))

    # Simulate a failing test run so the agent attempts a repair.
    monkeypatch.setattr(
        agent_module,
        "run_tests",
        lambda repository: {
            "passed": False,
            "return_code": 1,
            "output": "1 failed",
        },
    )

    # Simulate an AI proposal that tries to modify a test file.
    monkeypatch.setattr(
        instance,
        "propose_patch",
        lambda: {
            "success": True,
            "patch": {
                "file_path": "tests/test_app.py",
                "old_text": "assert 1 == 2",
                "new_text": "assert 1 == 1",
            },
        },
    )

    result = instance.apply_patch_with_test_gate()

    assert result["success"] is False
    assert "test files are not allowed" in result["message"]
    assert test_file.read_text(encoding="utf-8") == original


def test_repair_rolls_back_when_tests_still_fail(tmp_path, monkeypatch):
    from app import agent as agent_module
    from app.agent import Agent

    repository = tmp_path
    tests_dir = repository / "tests"
    tests_dir.mkdir()

    source = repository / "utils.py"
    original = (
        "def calculate_total(items):\n"
        "    return sum(items) + 10\n"
    )
    source.write_text(original, encoding="utf-8")

    test_file = tests_dir / "test_app.py"
    test_file.write_text(
        "from utils import calculate_total\n\n"
        "def test_calculate_total():\n"
        "    assert calculate_total([10, 20, 30]) == 60\n",
        encoding="utf-8",
    )

    agent = Agent(str(repository))

    # Supply a patch that does not fix the bug.
    monkeypatch.setattr(
        agent,
        "propose_patch",
        lambda: {
            "success": True,
            "patch": {
                "file_path": "utils.py",
                "old_text": "return sum(items) + 10",
                "new_text": "return sum(items) + 20",
            },
        },
    )

    # Keep the real pytest runner so both test runs are genuine.
    result = agent.apply_patch_with_test_gate()

    assert result["success"] is False
    assert result["rolled_back"] is True
    assert source.read_text(encoding="utf-8") == original


def test_successful_repair_reports_file_and_rollback_status(
    tmp_path, monkeypatch
):
    from app import agent as agent_module
    from app.agent import Agent

    repository = tmp_path
    source = repository / "utils.py"
    original = "def calculate_total(items):\n    return sum(items) + 10\n"
    fixed = "def calculate_total(items):\n    return sum(items)\n"
    source.write_text(original, encoding="utf-8")

    agent = Agent(str(repository))

    monkeypatch.setattr(
        agent_module,
        "run_tests",
        lambda repository: {"passed": False,
                            "return_code": 1, "output": "failed"},
    )
    monkeypatch.setattr(
        agent,
        "propose_patch",
        lambda: {
            "success": True,
            "patch": {
                "file_path": "utils.py",
                "old_text": "return sum(items) + 10",
                "new_text": "return sum(items)",
            },
        },
    )

    # The initial test run fails; the post-patch run passes.
    results = iter([
        {"passed": False, "return_code": 1, "output": "failed"},
        {"passed": True, "return_code": 0, "output": "passed"},
    ])
    monkeypatch.setattr(
        agent_module, "run_tests", lambda repository: next(results)
    )

    result = agent.apply_patch_with_test_gate()

    assert result["success"] is True
    assert result["rolled_back"] is False
    assert result["file_path"] == "utils.py"
    assert source.read_text(encoding="utf-8") == fixed


def test_generate_report_includes_test_summary(tmp_path, monkeypatch):
    from app import agent as agent_module
    from app.agent import Agent

    agent = Agent(str(tmp_path))

    snapshot = {
        "branch": "main",
        "status": "",
        "files": ["utils.py", "README.md"],
        "tests": {
            "passed": True,
            "return_code": 0,
            "output": "1 passed",
        },
    }

    monkeypatch.setattr(agent, "inspect_repository", lambda: snapshot)

    report = agent.generate_report()

    assert report["test_summary"] == "PASSED"
    assert report["tests_passed"] is True
    assert report["test_return_code"] == 0
    assert report["files_inspected"] == 2
    assert "does not prove the repository is bug-free" in report["diagnosis"]


def test_cli_report_command_prints_markdown(monkeypatch, capsys):
    from app import main as main_module

    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "report", "--repo", "examples/demo_repo"],
    )

    monkeypatch.setattr(
        main_module.Agent,
        "generate_report",
        lambda self: {
            "repository": "demo_repo",
            "branch": "master",
            "git_status": "",
            "files_inspected": 4,
            "test_summary": "PASSED",
            "tests_passed": True,
            "test_return_code": 0,
            "test_output": "1 passed",
            "diagnosis": "Tests passed.",
        },
    )

    monkeypatch.setattr(
        main_module.Agent,
        "format_report",
        lambda self, report: "# Engineering Analysis Report\n\nStatus: PASSED",
    )

    main_module.main()

    output = capsys.readouterr().out
    assert "# Engineering Analysis Report" in output
    assert "Status: PASSED" in output


def test_repair_history_saves_and_loads_records(tmp_path):
    from app.tools.history import (
        load_repair_history,
        save_repair_history,
    )

    history_file = str(tmp_path / "repair_history.json")

    first_record = {
        "file_path": "utils.py",
        "success": True,
        "rolled_back": False,
    }
    second_record = {
        "file_path": "app.py",
        "success": False,
        "rolled_back": True,
    }

    save_repair_history(first_record, history_file)
    save_repair_history(second_record, history_file)

    history = load_repair_history(history_file)

    assert len(history) == 2
    assert history[0] == first_record
    assert history[1] == second_record


def test_successful_repair_is_recorded(tmp_path, monkeypatch):
    import json
    from app import agent as agent_module
    from app.agent import Agent

    repository = tmp_path
    source = repository / "utils.py"
    source.write_text(
        "def calculate_total(items):\n    return sum(items) + 10\n",
        encoding="utf-8",
    )

    history_file = tmp_path / "history.json"
    monkeypatch.setattr(
        agent_module,
        "save_repair_history",
        lambda record: history_file.write_text(
            json.dumps(
                json.loads(history_file.read_text()) + [record]
                if history_file.exists()
                else [record]
            ),
            encoding="utf-8",
        ),
    )

    agent = Agent(str(repository))
    monkeypatch.setattr(
        agent,
        "propose_patch",
        lambda: {
            "success": True,
            "patch": {
                "file_path": "utils.py",
                "old_text": "return sum(items) + 10",
                "new_text": "return sum(items)",
            },
        },
    )

    results = iter([
        {"passed": False, "return_code": 1, "output": "failed"},
        {"passed": True, "return_code": 0, "output": "passed"},
    ])
    monkeypatch.setattr(
        agent_module, "run_tests", lambda repository: next(results)
    )

    result = agent.apply_patch_with_test_gate()
    history = json.loads(history_file.read_text(encoding="utf-8"))

    assert result["success"] is True
    assert len(history) == 1
    assert history[0]["file_path"] == "utils.py"
    assert history[0]["success"] is True
    assert history[0]["rolled_back"] is False
    assert history[0]["tests_passed"] is True


def test_rolled_back_repair_is_recorded(tmp_path, monkeypatch):
    import json
    from app import agent as agent_module
    from app.agent import Agent

    repository = tmp_path
    source = repository / "utils.py"
    original = "def calculate_total(items):\n    return sum(items) + 10\n"
    source.write_text(original, encoding="utf-8")

    history_file = tmp_path / "history.json"
    monkeypatch.setattr(
        agent_module,
        "save_repair_history",
        lambda record: history_file.write_text(
            json.dumps(
                json.loads(history_file.read_text()) + [record]
                if history_file.exists()
                else [record]
            ),
            encoding="utf-8",
        ),
    )

    agent = Agent(str(repository))
    monkeypatch.setattr(
        agent,
        "propose_patch",
        lambda: {
            "success": True,
            "patch": {
                "file_path": "utils.py",
                "old_text": "return sum(items) + 10",
                "new_text": "return sum(items) + 20",
            },
        },
    )

    results = iter([
        {"passed": False, "return_code": 1, "output": "failed"},
        {"passed": False, "return_code": 1, "output": "still failed"},
    ])
    monkeypatch.setattr(
        agent_module, "run_tests", lambda repository: next(results)
    )

    result = agent.apply_patch_with_test_gate()
    history = json.loads(history_file.read_text(encoding="utf-8"))

    assert result["rolled_back"] is True
    assert source.read_text(encoding="utf-8") == original
    assert len(history) == 1
    assert history[0]["success"] is False
    assert history[0]["rolled_back"] is True
    assert history[0]["tests_passed"] is False


def test_cli_history_command(monkeypatch, capsys):
    import json
    from app import main as main_module

    expected = [{"file_path": "utils.py", "success": True}]

    monkeypatch.setattr("sys.argv", ["main.py", "history"])
    monkeypatch.setattr(
        main_module, "load_repair_history", lambda: expected
    )

    main_module.main()

    assert json.loads(capsys.readouterr().out) == expected
