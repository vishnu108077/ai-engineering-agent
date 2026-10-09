import subprocess


def run_git_command(command: list[str], repository: str) -> str:
    """Run a read-only Git command and return its output."""
    result = subprocess.run(
        ["git", *command],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def get_status(repository: str) -> str:
    """Return the current Git status."""
    return run_git_command(
        ["status", "--short"],
        repository,
    )


def get_diff(repository: str) -> str:
    """Return the current Git diff."""
    return run_git_command(
        ["diff"],
        repository,
    )


def get_current_branch(repository: str) -> str:
    """Return the current Git branch."""
    return run_git_command(
        ["branch", "--show-current"],
        repository,
    )
