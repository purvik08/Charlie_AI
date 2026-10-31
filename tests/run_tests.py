#!/usr/bin/env python3
"""
Test runner for the Offline AI Assistant
"""

import subprocess
import sys
import os
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, os.path.abspath(PROJECT_ROOT))
import os
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print('='*60)

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: Test {test_file} timed out")
        return False
    except Exception as e:
        print(f"ERROR running {test_file}: {e}")
        return False

def main():
    """Run all test files"""
    test_dir = Path(__file__).parent

    # Find all test files
    test_files = list(test_dir.glob("test_*.py"))

    if not test_files:
        print("No test files found!")
        return 1

    print(f"Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f.name}")

    # Run each test file
    passed = 0
    failed = 0

    for test_file in test_files:
        if run_test_file(test_file):
            passed += 1
            print(f"[PASS] {test_file.name} PASSED")
        else:
            failed += 1
            print(f"[FAIL] {test_file.name} FAILED")

    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(test_files)}")

    if failed > 0:
        print(f"\n[FAIL] {failed} test(s) failed!")
        return 1
    else:
        print(f"\n[PASS] All {passed} test(s) passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())