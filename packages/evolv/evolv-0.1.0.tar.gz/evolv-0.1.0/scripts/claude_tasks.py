#!/usr/bin/env python3
"""
Claude Code Task Templates
==========================

This script provides common task templates that Claude Code can use
to be more efficient when working on the Evolve framework.

Usage:
    python scripts/claude_tasks.py <task_name> [args...]

Examples:
    python scripts/claude_tasks.py new_issue 42
    python scripts/claude_tasks.py find_usage "Program"
    python scripts/claude_tasks.py benchmark "async"
"""

import argparse
import subprocess
import sys
from pathlib import Path


class ClaudeTaskRunner:
    """Provides automated task templates for common development workflows."""

    def __init__(self):
        self.root = Path(__file__).parent.parent

    def new_issue(self, issue_number: int):
        """Start working on a new GitHub issue."""
        print(f"🎯 Starting work on issue #{issue_number}")

        # Read issue details
        subprocess.run(["gh", "issue", "view", str(issue_number)], check=True)

        # Create branch
        branch_name = f"feature/issue-{issue_number}"
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        # Check for issue specification
        issue_files = list(self.root.glob(f".github/issues/{issue_number}_*.md"))

        if issue_files:
            print(f"\n📄 Issue specification found: {issue_files[0]}")
            subprocess.run(["cat", str(issue_files[0])], check=True)

        print(f"\n✅ Ready to work on issue #{issue_number}")
        print("\nNext steps:")
        print("1. Read the issue specification carefully")
        print("2. Search for related code")
        print("3. Write failing tests")
        print("4. Implement the feature")
        print("5. Run 'make pr-ready' before submitting")

    def find_usage(self, class_name: str):
        """Find all usages of a class or function."""
        print(f"🔍 Finding all usages of '{class_name}'")

        # Search for imports
        print("\n📦 Import statements:")
        subprocess.run(["rg", f"from .* import.*{class_name}", "--type", "py"], cwd=self.root)
        subprocess.run(["rg", f"import.*{class_name}", "--type", "py"], cwd=self.root)

        # Search for instantiation
        print("\n🏗️ Instantiations:")
        subprocess.run(["rg", f"{class_name}\\(", "--type", "py"], cwd=self.root)

        # Search for type hints
        print("\n📝 Type hints:")
        subprocess.run(["rg", f": {class_name}", "--type", "py"], cwd=self.root)
        subprocess.run(["rg", f"\\[{class_name}", "--type", "py"], cwd=self.root)

    def benchmark(self, scenario: str = "simple"):
        """Run performance benchmarks."""
        print(f"📊 Running benchmark for scenario: {scenario}")

        # Create baseline
        print("\n📈 Creating baseline...")
        baseline_file = self.root / "benchmark_baseline.txt"
        with open(baseline_file, "w") as f:
            subprocess.run(
                ["./scripts/test_e2e.py", "--scenario", scenario, "--iterations", "5"],
                stdout=f,
                cwd=self.root,
                check=True,
            )

        print(f"\n✅ Baseline saved to {baseline_file}")
        print("\nNow make your changes and run:")
        print(f"python scripts/claude_tasks.py compare_benchmark {scenario}")

    def compare_benchmark(self, scenario: str = "simple"):
        """Compare current performance against baseline."""
        print(f"📊 Comparing performance for scenario: {scenario}")

        baseline_file = self.root / "benchmark_baseline.txt"
        if not baseline_file.exists():
            print("❌ No baseline found. Run 'benchmark' first.")
            return

        # Run current benchmark
        current_file = self.root / "benchmark_current.txt"
        with open(current_file, "w") as f:
            subprocess.run(
                ["./scripts/test_e2e.py", "--scenario", scenario, "--iterations", "5"],
                stdout=f,
                cwd=self.root,
                check=True,
            )

        # Compare results
        print("\n📈 Performance comparison:")
        subprocess.run(["diff", "-u", str(baseline_file), str(current_file)], cwd=self.root)

    def test_pattern(self, pattern: str):
        """Run tests matching a pattern."""
        print(f"🧪 Running tests matching pattern: {pattern}")
        subprocess.run(["uv", "run", "pytest", "-v", "-k", pattern], cwd=self.root, check=True)

    def debug_test(self, test_path: str):
        """Debug a specific test with detailed output."""
        print(f"🐛 Debugging test: {test_path}")
        subprocess.run(["uv", "run", "pytest", "-xvs", test_path, "--pdb-trace"], cwd=self.root, check=True)

    def quick_fix(self):
        """Apply common quick fixes."""
        print("🔧 Applying common quick fixes...")

        # Fix formatting
        print("\n📝 Fixing formatting...")
        subprocess.run(["uv", "run", "ruff", "format", "."], cwd=self.root, check=True)

        # Fix imports
        print("\n📦 Fixing imports...")
        subprocess.run(["uv", "run", "ruff", "check", "--select", "I", "--fix", "."], cwd=self.root, check=True)

        # Show remaining issues
        print("\n⚠️ Checking for remaining issues...")
        subprocess.run(["uv", "run", "ruff", "check", "."], cwd=self.root)

        print("\n✅ Quick fixes applied!")


def main():
    """Main entry point for task runner."""
    parser = argparse.ArgumentParser(description="Claude Code task automation")
    parser.add_argument("task", help="Task to run")
    parser.add_argument("args", nargs="*", help="Task arguments")

    args = parser.parse_args()

    runner = ClaudeTaskRunner()

    # Get the task method
    task_method = getattr(runner, args.task, None)
    if not task_method:
        print(f"❌ Unknown task: {args.task}")
        print("\nAvailable tasks:")
        for name in dir(runner):
            if not name.startswith("_"):
                method = getattr(runner, name)
                if callable(method) and method.__doc__:
                    print(f"  - {name}: {method.__doc__.strip()}")
        sys.exit(1)

    # Run the task
    try:
        task_method(*args.args)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Task failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
