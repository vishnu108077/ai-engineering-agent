from pathlib import Path
import json

from httpx import patch

from app.tools.patch import apply_text_patch
from app.tools.filesystem import list_files,read_file
from app.tools.git import get_current_branch, get_status
from app.tools.tests import run_tests
from app.llm import ask_ai

class Agent:
    """Coordinate repository inspection tools."""

    def __init__(self, repository: str):
        self.repository = repository

    def inspect_repository(self) -> dict:
        """Collect a snapshot of the repository."""
        return {
            "branch": get_current_branch(self.repository),
            "status": get_status(self.repository),
            "files": list_files(self.repository),
            "tests": run_tests(self.repository),
        }

    def analyze_failure(self) -> str:
        """Ask Gemini to analyze the repository's test failure."""
        snapshot = self.inspect_repository()

        if snapshot["tests"]["passed"]:
            return "All tests passed. No test failure to analyze."

        source_code = ""
        for file_name in snapshot["files"]:
            if file_name.endswith(".py"):
                from app.tools.filesystem import read_file

                file_path = f"{self.repository}/{file_name}"
                source_code += f"\n--- {file_name} ---\n"
                source_code += read_file(file_path)

        prompt = f"""
You are a software engineer diagnosing a Python test failure.

Repository branch: {snapshot["branch"]}
Git status: {snapshot["status"]}

Source code:
{source_code}

Test output:
{snapshot["tests"]["output"]}

Explain:
1. What caused the failure?
2. Which file and line are likely responsible?
3. What minimal fix do you recommend?

Do not claim you ran tests or changed files.
"""

        return ask_ai(prompt)

    def propose_patch(self) -> dict:
        """Ask Gemini to propose a structured code patch."""
        diagnosis = self.analyze_failure()

        if diagnosis.startswith("All tests passed"):
            return {
                "success": False,
                "message": "No failing test to diagnose.",
            }

        prompt = f"""
You are a careful Python software engineer.

Based on this diagnosis, propose one minimal code patch.

Diagnosis:
{diagnosis}

Return ONLY a valid JSON object with these exact fields:
{{
  "file_path": "relative path inside the repository",
  "old_text": "exact existing text to replace",
  "new_text": "replacement text"
}}

Rules:
- Do not use Markdown code fences.
- Do not include explanations outside the JSON.
- Do not invent file contents.
- Keep the change as small as possible.
"""

        response_text = ask_ai(prompt)

        try:
            patch = json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Gemini did not return valid JSON.",
                "response": response_text,
            }

        required_fields = {"file_path", "old_text", "new_text"}

        if not isinstance(patch, dict) or not required_fields.issubset(patch):
            return {
                "success": False,
                "message": "Gemini's patch is missing required fields.",
            }

        if not all(
            isinstance(patch[field], str) and patch[field]
            for field in required_fields
        ):
            return {
                "success": False,
                "message": "Patch fields must be non-empty strings.",
            }

        return {
            "success": True,
            "patch": patch,
        }

    def apply_patch_with_test_gate(self) -> dict:
        """Apply an AI patch only if tests pass; otherwise restore the file."""
        initial_tests = run_tests(self.repository)

        if initial_tests["passed"]:
            return {
                "success": False,
                "message": "No repair needed: all tests already pass.",
                "tests": initial_tests,
            }
        proposal = self.propose_patch()

        if not proposal.get("success"):
            return {
                "success": False,
                "message": "Patch proposal failed.",
                "details": proposal,
            }

        patch = proposal["patch"]

        # Never allow an AI-generated patch to modify test files.
        patch_path = Path(patch["file_path"])

        if (
            patch_path.is_absolute()
            or "tests" in patch_path.parts
            or patch_path.name.startswith("test_")
        ):
            return {
                "success": False,
                "message": "Rejected: patches to test files are not allowed.",
            }

        repository_root = Path(self.repository).resolve()
        target_path = (repository_root / patch_path).resolve()


        # Do not allow the AI to target files outside the repository.
        if not target_path.is_relative_to(repository_root):
            return {
                "success": False,
                "message": "Rejected: target is outside the repository.",
            }

        if not target_path.is_file():
            return {
                "success": False,
                "message": "Rejected: target must be an existing file.",
            }

        # Keep the original contents so we can restore them if tests fail.
        original_content = target_path.read_bytes()

        apply_result = apply_text_patch(
            self.repository,
            patch["file_path"],
            patch["old_text"],
            patch["new_text"],
            dry_run=False,
        )

        if not apply_result.get("applied"):
            return {
                "success": False,
                "message": "Patch was not applied.",
                "details": apply_result,
            }

        try:
            test_result = run_tests(self.repository)
            if test_result["passed"]:
                return {
                            "success": True,
                            "rolled_back": False,
                            "file_path": patch["file_path"],
                            "message": "Patch applied and tests passed.",
                            "tests": test_result,
                }


            # Restore the original file if tests fail.
            target_path.write_bytes(original_content)

            return {
                            "success": False,
                            "rolled_back": True,
                            "file_path": patch["file_path"],
                            "message": "Tests failed; original file was restored.",
                            "tests": test_result,
                    }


        except Exception as error:
            # Attempt to restore the original file after an unexpected error.
            target_path.write_bytes(original_content)

            return {
                "success": False,
                "rolled_back": True,
                "message": "An error occurred; original file was restored.",
                "error": str(error),
            }


    def generate_report(self) -> dict:
        """Generate a structured engineering report."""
        snapshot = self.inspect_repository()

        if snapshot["tests"]["passed"]:
            diagnosis = (
                "Tests passed. No current test failure was detected. "
                "This does not prove the repository is bug-free."
            )
        else:
            diagnosis = self.analyze_failure()

        return {
            "repository": self.repository,
            "branch": snapshot["branch"],
            "git_status": snapshot["status"],
            "files_inspected": len(snapshot["files"]),
            "tests_passed": snapshot["tests"]["passed"],
            "test_output": snapshot["tests"]["output"],
            "diagnosis": diagnosis,
        }

    def format_report(self, report: dict) -> str:
        """Convert a structured report into readable Markdown."""
        test_status = "PASSED" if report["tests_passed"] else "FAILED"

        return f"""# Engineering Analysis Report

## Repository
- **Path:** {report["repository"]}
- **Branch:** {report["branch"]}
- **Modified files:** {report["git_status"] or "None detected"}
- **Python files inspected:** {report["files_inspected"]}

## Test Results
- **Status:** {test_status}

## Diagnosis
{report["diagnosis"]}

## Raw Test Output
```text
{report["test_output"]}
```
"""
