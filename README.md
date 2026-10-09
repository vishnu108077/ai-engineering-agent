# AI Engineering Automation Agent

An AI-assisted software engineering tool that inspects Python repositories, diagnoses test failures with Gemini, proposes code patches, and validates changes using automated tests.

The project demonstrates practical AI engineering, Python development, test automation, Git integration, defensive file handling, and recovery from failed changes.

## Features

- **Repository inspection:** Lists relevant files and inspects Git branch and working-tree status.
- **Automated testing:** Runs pytest against a target repository and captures the results.
- **AI-assisted diagnosis:** Uses Gemini to analyze test failures and suggest likely causes.
- **Structured patch proposals:** Requests machine-readable code changes from the AI.
- **Patch safety checks:** Requires an exact text match, rejects ambiguous replacements, prevents paths outside the target repository, and blocks patches to test files.
- **Test-gated repairs:** Keeps a proposed code change only when the subsequent test run passes.
- **Rollback:** Restores the original file if tests fail after a patch is applied.
- **Engineering reports:** Generates a Markdown report with repository details, test status, diagnosis, and test output.
- **Repair history:** Stores repair outcomes in JSON and provides a CLI command to view saved history.

## Architecture

```text
Command-line interface
        |
        v
      Agent
        |
        +--> Filesystem tools
        +--> Git tools
        +--> Pytest runner
        +--> Gemini integration
        +--> Safe patch application
        +--> Repair history
        +--> Engineering reports
```

The CLI coordinates the agent, while separate tool modules handle filesystem operations, Git inspection, testing, patch application, and repair-history persistence.

## Requirements

- Python 3.11+
- Git
- A Gemini API key
- Python dependencies listed in `requirements.txt`

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/vishnu108077/ai-engineering-agent.git
cd ai-engineering-agent
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

Do not commit `.env` or publish your API key.

## Usage

Run commands from the project root.

Inspect a repository:

```bash
python -m app.main inspect --repo examples/demo_repo
```

Analyze test failures:

```bash
python -m app.main analyze --repo examples/demo_repo
```

Attempt a test-gated repair:

```bash
python -m app.main repair --repo examples/demo_repo
```

Generate an engineering report:

```bash
python -m app.main report --repo examples/demo_repo
```

View saved repair history:

```bash
python -m app.main history
```

Display CLI help:

```bash
python -m app.main --help
```
## Demo Walkthrough

The repository includes a small demo project at `examples/demo_repo` for exercising the agent's inspection and reporting workflows.

### 1. Run the automated tests

```bash
pytest
```

Expected result: all 13 project tests pass.

### 2. Inspect the demo repository

```bash
python -m app.main inspect --repo examples/demo_repo
```

The agent reports the Git branch, working-tree status, discovered files, and test results.

### 3. Generate an engineering report

```bash
python -m app.main report --repo examples/demo_repo
```

The Markdown report includes repository information, test status, diagnosis, and raw test output.

### 4. Attempt an automated repair

```bash
python -m app.main repair --repo examples/demo_repo
```

The agent skips repair if tests already pass. If tests fail, it requests a patch proposal and applies safety checks. A patch is retained only if the subsequent test run succeeds; otherwise, the original file is restored.

### What this demonstrates

- Python CLI design and modular tool integration
- AI-assisted debugging and structured patch proposals
- Automated testing and defensive file handling
- Test-gated changes and rollback behavior
- Engineering reporting and JSON-based repair history

The demo is a development example, not a guarantee that every AI-proposed repair will be correct. Review proposed changes before using the agent on important repositories.
## Testing

Run the project's automated test suite:

```bash
pytest
```

The tests cover patch application, rejection of unsafe targets, rollback behavior, report generation, CLI behavior, and repair-history persistence.

## Safety and limitations

- AI-generated patches should be treated as untrusted proposals.
- Patch application requires exactly one match for the original text.
- Patches targeting test files or paths outside the authorized repository are rejected.
- A patch is retained only if the post-patch test run succeeds; otherwise, the original target file is restored.
- Passing tests do not prove that the repository is free of defects.
- Test success does not guarantee that a patch is correct, secure, or complete.
- Repair history is stored locally as JSON. It should not be treated as a tamper-proof audit log.
- Review AI-generated changes before using this tool on important repositories.

## Technology stack

- Python
- Gemini API
- pytest
- Git
- JSON
- Command-line tooling

## Project goals

This project explores how AI can assist software engineering workflows while keeping deterministic tools, automated tests, and explicit safety checks responsible for validating changes.