#!/usr/bin/env python3
"""
End-to-End Security Tests for Synth Mind
Tests all security fixes from the security audit.
"""

import sys
import os
import time
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools import ToolManager


def run_test(name: str, test_func) -> dict:
    """Run a single test and return result."""
    try:
        result = test_func()
        return {"name": name, "passed": result["passed"], "message": result["message"]}
    except Exception as e:
        return {"name": name, "passed": False, "message": f"Exception: {type(e).__name__}: {e}"}


def test_command_injection_semicolon() -> dict:
    """Test 1: Command injection via semicolon is blocked."""
    tm = ToolManager()
    result = tm._shell_run("ls; cat /etc/passwd")

    # Should fail - shlex.split will parse this as args to ls, not separate commands
    # With shell=False, semicolon is treated literally
    if not result["success"] and "Command not found" not in str(result.get("error", "")):
        return {"passed": True, "message": "Semicolon injection blocked (treated as literal arg)"}
    elif result["success"] and "root:" not in result.get("stdout", ""):
        return {"passed": True, "message": "Semicolon treated as literal, no injection"}
    else:
        return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_backtick_substitution() -> dict:
    """Test 2: Backtick command substitution treated as literal."""
    tm = ToolManager()
    result = tm._shell_run("echo `whoami`")

    if result["success"]:
        stdout = result.get("stdout", "")
        # With shell=False, backticks are treated literally
        if "`whoami`" in stdout or stdout.strip() == "`whoami`":
            return {"passed": True, "message": "Backticks treated as literal text"}
        elif "root" not in stdout and os.getenv("USER", "user") not in stdout:
            return {"passed": True, "message": "Command substitution not executed"}

    return {"passed": False, "message": f"Result: {result}"}


def test_path_traversal_blocked() -> dict:
    """Test 3: Path traversal (../) is blocked."""
    tm = ToolManager()
    result = tm._shell_run("head ../../../etc/passwd")

    if not result["success"]:
        error = result.get("error", "")
        if "disallowed path pattern" in error or "must be within workspace" in error:
            return {"passed": True, "message": "Path traversal blocked correctly"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_sensitive_paths_blocked() -> dict:
    """Test 4: Access to sensitive paths (/etc/) is blocked."""
    tm = ToolManager()
    result = tm._shell_run("head /etc/passwd")

    if not result["success"]:
        error = result.get("error", "")
        if "disallowed path pattern" in error:
            return {"passed": True, "message": "Sensitive path /etc/ blocked"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_find_command_removed() -> dict:
    """Test 5: 'find' command removed from allowlist."""
    tm = ToolManager()
    result = tm._shell_run("find . -exec cat /etc/passwd \\;")

    if not result["success"]:
        error = result.get("error", "")
        if "not allowed" in error:
            return {"passed": True, "message": "'find' command correctly removed from allowlist"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_grep_command_removed() -> dict:
    """Test 6: 'grep' command removed from allowlist."""
    tm = ToolManager()
    result = tm._shell_run("grep -r password /etc/")

    if not result["success"]:
        error = result.get("error", "")
        if "not allowed" in error:
            return {"passed": True, "message": "'grep' command correctly removed from allowlist"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_calculator_blocks_import() -> dict:
    """Test 7: Calculator AST parser blocks __import__."""
    tm = ToolManager()
    result = tm._calculator("__import__('os').system('whoami')")

    if not result["success"]:
        error = result.get("error", "")
        # AST parser blocks this as either unknown function or invalid call pattern
        if any(msg in error for msg in ["Unknown function", "Unsupported", "Invalid", "simple function calls"]):
            return {"passed": True, "message": f"Calculator blocks __import__ injection: {error}"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_sandbox_blocks_open() -> dict:
    """Test 8: Code sandbox blocks 'open' builtin."""
    tm = ToolManager()
    result = tm._code_execute("print(open('/etc/passwd').read())")

    if not result["success"]:
        error = result.get("error", "")
        if "open" in error.lower() or "name" in error.lower() or "defined" in error.lower():
            return {"passed": True, "message": "Sandbox blocks 'open' builtin"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_sandbox_blocks_os_import() -> dict:
    """Test 9: Code sandbox blocks 'os' module import."""
    tm = ToolManager()
    result = tm._code_execute("import os; print(os.listdir('/'))")

    if not result["success"]:
        error = result.get("error", "")
        if "not allowed" in error or "ImportError" in error:
            return {"passed": True, "message": "Sandbox blocks 'os' module import"}

    return {"passed": False, "message": f"VULNERABLE: {result}"}


def test_sandbox_timeout_enforcement() -> dict:
    """Test 10: Code sandbox enforces timeout on infinite loops."""
    tm = ToolManager()
    start_time = time.time()
    result = tm._code_execute("while True: pass")
    elapsed = time.time() - start_time

    if not result["success"]:
        if result.get("timed_out") or "timed out" in result.get("error", "").lower():
            if elapsed < 15:  # Should timeout in ~10 seconds
                return {"passed": True, "message": f"Timeout enforced in {elapsed:.1f}s"}

    if elapsed > 15:
        return {"passed": False, "message": f"Timeout took too long: {elapsed:.1f}s"}

    return {"passed": False, "message": f"VULNERABLE: No timeout enforced. Result: {result}"}


def main():
    """Run all security tests."""
    print("=" * 60)
    print("SYNTH MIND - End-to-End Security Tests")
    print("=" * 60)
    print()

    tests = [
        ("1. Command injection (semicolon)", test_command_injection_semicolon),
        ("2. Backtick substitution", test_backtick_substitution),
        ("3. Path traversal (../) blocked", test_path_traversal_blocked),
        ("4. Sensitive paths (/etc/) blocked", test_sensitive_paths_blocked),
        ("5. 'find' command removed", test_find_command_removed),
        ("6. 'grep' command removed", test_grep_command_removed),
        ("7. Calculator blocks __import__", test_calculator_blocks_import),
        ("8. Sandbox blocks 'open'", test_sandbox_blocks_open),
        ("9. Sandbox blocks 'os' import", test_sandbox_blocks_os_import),
        ("10. Sandbox timeout enforcement", test_sandbox_timeout_enforcement),
    ]

    results = []
    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"Running: {name}...", end=" ", flush=True)
        result = run_test(name, test_func)
        results.append(result)

        if result["passed"]:
            print(f"✓ PASSED")
            print(f"   {result['message']}")
            passed += 1
        else:
            print(f"✗ FAILED")
            print(f"   {result['message']}")
            failed += 1
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total:  {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    if failed == 0:
        print("🎉 ALL SECURITY TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {failed} SECURITY TEST(S) FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
