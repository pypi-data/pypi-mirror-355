#!/usr/bin/env python
"""End-to-end testing script for the Evolve framework.

This script runs comprehensive tests with real external APIs to validate
the entire evolution workflow. It's designed for local validation only.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test scenario."""

    scenario: str
    success: bool
    iterations_run: int
    initial_fitness: Optional[float]
    final_fitness: Optional[float]
    improvement: Optional[float]
    duration_seconds: float
    error: Optional[str] = None
    evolution_enabled: bool = True
    variants_generated: int = 0


@dataclass
class TestReport:
    """Overall test report."""

    timestamp: str
    total_scenarios: int
    passed: int
    failed: int
    results: List[TestResult]
    environment: Dict[str, str]


class E2ETestRunner:
    """Runs end-to-end tests for the Evolve framework."""

    def __init__(self, verbose: bool = False, executor: str = "modal"):
        self.verbose = verbose
        self.executor = executor
        self.results: List[TestResult] = []
        self.start_time = time.time()

    def setup_logging(self):
        """Configure logging for the test run."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("e2e_test.log", mode="w"),
            ],
        )

        # Reduce noise from external libraries
        for lib in ["httpx", "LiteLLM", "modal", "aider"]:
            logging.getLogger(lib).setLevel(logging.WARNING)

    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Validate that all required dependencies are available."""
        issues = []

        # Check environment variables
        required_vars = ["OPEN_ROUTER_API_KEY"]
        if self.executor == "modal":
            required_vars.append("MODAL_TOKEN_ID")

        for var in required_vars:
            if not os.environ.get(var):
                issues.append(f"Missing environment variable: {var}")

        # Check Aider installation
        try:
            subprocess.run(["aider", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            issues.append("Aider not installed. Run: uv tool install aider-chat")

        # Check Modal CLI if using Modal executor
        if self.executor == "modal":
            try:
                subprocess.run(["modal", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                issues.append("Modal CLI not installed. Run: pip install modal")

        return len(issues) == 0, issues

    def run_scenario(self, scenario_path: str, iterations: int = 3) -> TestResult:
        """Run a single test scenario."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Running scenario: {scenario_path}")
        logger.info(f"{'=' * 60}")

        start_time = time.time()
        scenario_name = Path(scenario_path).stem

        # Set up environment
        env = os.environ.copy()
        env.update(
            {
                "EVOLVE": "1",
                "EVOLVE_ITERATIONS": str(iterations),
                "EVOLVE_EXECUTOR_TYPE": self.executor,
                "EVOLVE_PARALLEL": "2",  # Conservative for testing
                "PRIMARY_METRIC": "fitness",
            }
        )

        try:
            # Run the scenario
            cmd = [sys.executable, scenario_path]
            logger.info(f"Executing: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout

            if process.returncode != 0:
                raise RuntimeError(f"Process failed with code {process.returncode}: {stderr}")

            # Parse evolution results from output
            result = self._parse_evolution_output(stdout, stderr)
            result.scenario = scenario_name
            result.duration_seconds = time.time() - start_time

            if result.success and result.initial_fitness and result.final_fitness:
                result.improvement = (result.final_fitness - result.initial_fitness) / result.initial_fitness * 100
                logger.info(
                    f"✓ Evolution successful: {result.initial_fitness:.4f} → "
                    f"{result.final_fitness:.4f} ({result.improvement:+.1f}%)"
                )
            else:
                logger.error(f"✗ Evolution failed: {result.error}")

            return result

        except subprocess.TimeoutExpired:
            logger.error(f"Scenario {scenario_name} timed out")
            return TestResult(
                scenario=scenario_name,
                success=False,
                iterations_run=0,
                initial_fitness=None,
                final_fitness=None,
                improvement=None,
                duration_seconds=time.time() - start_time,
                error="Timeout after 5 minutes",
            )
        except Exception as e:
            logger.error(f"Error running scenario {scenario_name}: {e}")
            return TestResult(
                scenario=scenario_name,
                success=False,
                iterations_run=0,
                initial_fitness=None,
                final_fitness=None,
                improvement=None,
                duration_seconds=time.time() - start_time,
                error=str(e),
            )

    def _parse_evolution_output(self, stdout: str, stderr: str) -> TestResult:
        """Parse evolution results from process output."""
        lines = stdout.split("\n")

        # Look for evolution markers
        initial_fitness = None
        final_fitness = None
        iterations_run = 0
        variants_generated = 0
        evolution_enabled = False

        for line in lines:
            # Check if evolution was enabled
            if "Starting evolution process" in line or "Evolution iteration" in line:
                evolution_enabled = True

            # Parse initial fitness
            if "Initial program fitness:" in line or "Seed program fitness:" in line:
                try:
                    initial_fitness = float(line.split(":")[-1].strip())
                except ValueError:
                    pass

            # Parse iteration count
            if "Evolution iteration" in line:
                try:
                    iterations_run = max(iterations_run, int(line.split()[2].strip(":")))
                except (IndexError, ValueError):
                    pass

            # Parse variants generated
            if "variants generated" in line:
                try:
                    variants_generated += int(line.split()[0])
                except (IndexError, ValueError):
                    pass

            # Parse final/best fitness
            if "Best fitness:" in line or "Final best fitness:" in line:
                try:
                    final_fitness = float(line.split(":")[-1].strip())
                except ValueError:
                    pass

        # If no evolution markers found, check if it ran at all
        if not evolution_enabled:
            return TestResult(
                scenario="",
                success=False,
                iterations_run=0,
                initial_fitness=None,
                final_fitness=None,
                improvement=None,
                duration_seconds=0,
                error="Evolution was not enabled or did not run",
                evolution_enabled=False,
            )

        # Consider success if we got both initial and final fitness
        success = initial_fitness is not None and final_fitness is not None

        return TestResult(
            scenario="",
            success=success,
            iterations_run=iterations_run,
            initial_fitness=initial_fitness,
            final_fitness=final_fitness,
            improvement=None,
            duration_seconds=0,
            error=None if success else "Failed to parse fitness values",
            evolution_enabled=evolution_enabled,
            variants_generated=variants_generated,
        )

    def run_all_scenarios(self, scenarios: Optional[List[str]] = None) -> TestReport:
        """Run all test scenarios."""
        if scenarios is None:
            # Default scenarios
            scenarios = [
                "examples/simple_example.py",
                "examples/breast_cancer_example.py",
                "examples/regression_example.py",
                "examples/custom_fitness_example.py",
                "examples/map_elites_example.py",
                "examples/island_evolution_example.py",
                "examples/heterogeneous_islands_example.py",
            ]

        # Filter to existing files
        scenarios = [s for s in scenarios if Path(s).exists()]

        logger.info(f"Running {len(scenarios)} test scenarios")

        for scenario in scenarios:
            result = self.run_scenario(scenario)
            self.results.append(result)

        # Generate report
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed

        report = TestReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_scenarios=len(self.results),
            passed=passed,
            failed=failed,
            results=self.results,
            environment={
                "executor": self.executor,
                "python_version": sys.version,
                "evolve_parallel": os.environ.get("EVOLVE_PARALLEL", "4"),
            },
        )

        return report

    def save_report(self, report: TestReport, output_path: str = "e2e_report.json"):
        """Save test report to JSON file."""
        with open(output_path, "w") as f:
            json.dump(asdict(report), f, indent=2)
        logger.info(f"Report saved to {output_path}")

    def print_summary(self, report: TestReport):
        """Print a summary of test results."""
        print("\n" + "=" * 80)
        print("E2E TEST SUMMARY")
        print("=" * 80)
        print(f"Total scenarios: {report.total_scenarios}")
        print(f"Passed: {report.passed} ✓")
        print(f"Failed: {report.failed} ✗")
        print(f"Success rate: {report.passed / report.total_scenarios * 100:.1f}%")
        print(f"Total duration: {time.time() - self.start_time:.1f}s")
        print("\nResults by scenario:")
        print("-" * 80)

        for result in report.results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.scenario:30} ", end="")

            if result.success and result.improvement is not None:
                print(f"Improvement: {result.improvement:+6.1f}% ", end="")
                print(f"({result.initial_fitness:.4f} → {result.final_fitness:.4f})")
            else:
                print(f"Error: {result.error}")

        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run end-to-end tests for Evolve framework")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        help="Specific scenarios to run (default: all examples)",
    )
    parser.add_argument(
        "--executor",
        choices=["modal", "local"],
        default="modal",
        help="Executor type to use",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of evolution iterations per scenario",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--output",
        default="e2e_report.json",
        help="Output file for test report",
    )

    args = parser.parse_args()

    # Create test runner
    runner = E2ETestRunner(verbose=args.verbose, executor=args.executor)
    runner.setup_logging()

    # Validate environment
    logger.info("Validating environment...")
    valid, issues = runner.validate_environment()
    if not valid:
        logger.error("Environment validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        sys.exit(1)

    logger.info("Environment validation passed ✓")

    # Set iterations in environment
    os.environ["EVOLVE_ITERATIONS"] = str(args.iterations)

    # Run tests
    try:
        report = runner.run_all_scenarios(args.scenarios)
        runner.save_report(report, args.output)
        runner.print_summary(report)

        # Exit with appropriate code
        sys.exit(0 if report.failed == 0 else 1)

    except KeyboardInterrupt:
        logger.warning("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
