
import argparse
import json

from app.agent import Agent


def main():
    parser = argparse.ArgumentParser(
        description="AI Engineering Automation Agent"
    )

    parser.add_argument(
        "command",
        choices=["inspect", "analyze", "repair"],
        help="Action to perform on the target repository",
    )

    parser.add_argument(
        "--repo",
        default="examples/demo_repo",
        help="Path to the repository to inspect",
    )

    args = parser.parse_args()
    agent = Agent(args.repo)

    if args.command == "inspect":
        result = agent.inspect_repository()

    elif args.command == "analyze":
        result = {"diagnosis": agent.analyze_failure()}

    elif args.command == "repair":
        result = agent.apply_patch_with_test_gate()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
