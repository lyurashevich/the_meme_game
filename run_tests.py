#!/usr/bin/env python3
"""
Test runner script for the Meme Game project.
Provides different test configurations and options.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for the Meme Game project")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage reporting"
    )
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--class", dest="test_class", help="Run specific test class")
    parser.add_argument("--function", help="Run specific test function")
    parser.add_argument("--markers", help="Run tests with specific markers")
    parser.add_argument(
        "--install-deps", action="store_true", help="Install test dependencies first"
    )

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    import os

    os.chdir(project_dir)

    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"],
            "Installing test dependencies",
        ):
            return 1

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])

    # Add specific test selection
    if args.file:
        cmd.append(f"tests/{args.file}")
    elif args.test_class:
        cmd.extend(["-k", args.test_class])
    elif args.function:
        cmd.extend(["-k", args.function])
    elif args.markers:
        cmd.extend(["-m", args.markers])
    else:
        # Run all tests by default
        cmd.append("tests/")

    # Add type-specific markers
    if args.type == "unit":
        cmd.extend(["-m", "not integration"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])

    # Run the tests
    success = run_command(cmd, f"Running {args.type} tests")

    if success:
        print(f"\n{'='*60}")
        print("✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
        print(f"{'='*60}")
        return 0
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print(f"{'='*60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

