import os
import subprocess
from pathlib import Path


def run_tests(repository: str) -> dict:
    """Run pytest in a repository and return the test result."""
    repository_path = Path(repository).resolve()

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository_path)

    result = subprocess.run(
        [
            "pytest",
            "-c",
            "/dev/null",
            "--rootdir",
            str(repository_path),
        ],
        cwd=repository_path,
        capture_output=True,
        text=True,
        env=environment,
    )

    output = result.stdout

    if result.stderr:
        output += f"\n{result.stderr}"

    return {
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "output": output.strip(),
    }
