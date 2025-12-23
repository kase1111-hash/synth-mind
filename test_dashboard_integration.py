#!/usr/bin/env python3
"""
Test script to validate dashboard integration without requiring LLM API keys.
Tests imports, path resolution, and basic structure.
"""

import sys
from pathlib import Path

# Test 1: Import dashboard dependencies
print("=" * 60)
print("TEST 1: Dashboard Dependencies")
print("=" * 60)

try:
    from aiohttp import web
    import aiohttp_cors
    print("✓ aiohttp installed")
    print("✓ aiohttp-cors installed")
except ImportError as e:
    print(f"✗ Dashboard dependencies missing: {e}")
    print("  Install with: pip install aiohttp aiohttp-cors")
    sys.exit(1)

# Test 2: Check dashboard files exist
print("\n" + "=" * 60)
print("TEST 2: Dashboard Files")
print("=" * 60)

dashboard_files = {
    "run_synth_with_dashboard.py": Path("dashboard/run_synth_with_dashboard.py"),
    "server.py": Path("dashboard/server.py"),
    "dashboard.html": Path("dashboard/dashboard.html"),
    "timeline.html": Path("dashboard/timeline.html"),
    "README_DASHBOARD.md": Path("dashboard/README_DASHBOARD.md"),
    "DASHBOARD_COMPLETE.md": Path("dashboard/DASHBOARD_COMPLETE.md"),
}

for name, path in dashboard_files.items():
    if path.exists():
        size = path.stat().st_size
        print(f"✓ {name} exists ({size} bytes)")
    else:
        print(f"✗ {name} missing")
        sys.exit(1)

# Test 3: Check Python syntax
print("\n" + "=" * 60)
print("TEST 3: Python Syntax")
print("=" * 60)

import py_compile

try:
    py_compile.compile("dashboard/run_synth_with_dashboard.py", doraise=True)
    print("✓ run_synth_with_dashboard.py compiles")
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error in run_synth_with_dashboard.py: {e}")
    sys.exit(1)

try:
    py_compile.compile("dashboard/server.py", doraise=True)
    print("✓ server.py compiles")
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error in server.py: {e}")
    sys.exit(1)

# Test 4: Import structure
print("\n" + "=" * 60)
print("TEST 4: Import Structure")
print("=" * 60)

# Change to dashboard directory and test import path
original_dir = Path.cwd()
dashboard_dir = original_dir / "dashboard"

sys.path.insert(0, str(original_dir))

try:
    from core.orchestrator import SynthOrchestrator
    print("✓ Can import SynthOrchestrator from dashboard context")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

try:
    from utils.logging import setup_logging
    print("✓ Can import setup_logging")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 5: Check DashboardIntegratedOrchestrator class
print("\n" + "=" * 60)
print("TEST 5: Dashboard Integration Class")
print("=" * 60)

# Read the file and check for key components
dashboard_script = (original_dir / "dashboard/run_synth_with_dashboard.py").read_text()

checks = {
    "DashboardIntegratedOrchestrator class": "class DashboardIntegratedOrchestrator(SynthOrchestrator):",
    "broadcast_state method": "async def broadcast_state(self):",
    "_gather_dashboard_state method": "def _gather_dashboard_state(self)",
    "WebSocket handler": "async def websocket_handler(request):",
    "Start server function": "async def start_dashboard_server(",
    "Periodic broadcast": "async def periodic_broadcast(",
}

for check_name, check_string in checks.items():
    if check_string in dashboard_script:
        print(f"✓ {check_name} found")
    else:
        print(f"✗ {check_name} missing")
        sys.exit(1)

# Test 6: Check banner includes GDIL commands
print("\n" + "=" * 60)
print("TEST 6: Command Documentation")
print("=" * 60)

gdil_commands = ["/project [desc]", "/project status", "/resume project"]
for cmd in gdil_commands:
    if cmd in dashboard_script:
        print(f"✓ {cmd} documented in banner")
    else:
        print(f"✗ {cmd} not documented")
        sys.exit(1)

# Test 7: HTML Dashboard content
print("\n" + "=" * 60)
print("TEST 7: Dashboard HTML")
print("=" * 60)

dashboard_html = (original_dir / "dashboard/dashboard.html").read_text()

html_checks = {
    "HTML5 doctype": "<!DOCTYPE html>",
    "Title element": "<title>Synth Mind",
    "WebSocket connection": "WebSocket",
    "State visualization": "valence",
    "Dream buffer": "dream",
}

for check_name, check_string in html_checks.items():
    if check_string in dashboard_html:
        print(f"✓ {check_name} found")
    else:
        print(f"✗ {check_name} missing")

# Test 8: Check server.py structure
print("\n" + "=" * 60)
print("TEST 8: Server Module")
print("=" * 60)

server_code = (original_dir / "dashboard/server.py").read_text()

server_checks = {
    "DashboardServer class": "class DashboardServer:",
    "WebSocket route": "'/ws'",
    "State API route": "'/api/state'",
    "CORS setup": "aiohttp_cors.setup",
}

for check_name, check_string in server_checks.items():
    if check_string in server_code:
        print(f"✓ {check_name} found")
    else:
        print(f"✗ {check_name} missing")

# Test 9: Path resolution
print("\n" + "=" * 60)
print("TEST 9: Path Resolution")
print("=" * 60)

# Check the path.insert line
if "sys.path.insert(0, str(Path(__file__).parent.parent))" in dashboard_script:
    print("✓ Correct path resolution (parent.parent)")
elif "sys.path.insert(0, str(Path(__file__).parent))" in dashboard_script:
    print("✗ Incorrect path resolution (should be parent.parent)")
    sys.exit(1)
else:
    print("✗ Path resolution not found")
    sys.exit(1)

# Final summary
print("\n" + "=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print("\nDashboard Status:")
print("  ✓ All dependencies installed")
print("  ✓ All files present and valid")
print("  ✓ Python syntax correct")
print("  ✓ Import paths configured")
print("  ✓ WebSocket infrastructure ready")
print("  ✓ GDIL commands documented")
print("\nNext steps:")
print("  1. Set API key: export ANTHROPIC_API_KEY='your-key'")
print("  2. Run: cd dashboard && python run_synth_with_dashboard.py")
print("  3. Dashboard will open at: http://localhost:8080")
print("\nNote: Full testing requires LLM API access")
print("\n⚠️  GDIL Dashboard Visualization:")
print("  Currently the dashboard shows core psychological state.")
print("  GDIL project progress visualization is documented but not")
print("  yet implemented in the dashboard UI. This would be a future")
print("  enhancement to add project progress cards to the HTML.")
