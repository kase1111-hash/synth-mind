#!/usr/bin/env python3
"""
Test script to validate GDIL integration without requiring LLM API keys.
Tests the structure, imports, and basic initialization.
"""

import sys
from pathlib import Path

# Test 1: Import all modules
print("=" * 60)
print("TEST 1: Module Imports")
print("=" * 60)

try:
    from psychological.goal_directed_iteration import GoalDirectedIterationLoop, ProjectPhase
    print("✓ GDIL module imported successfully")
except Exception as e:
    print(f"✗ GDIL import failed: {e}")
    sys.exit(1)

try:
    from core.orchestrator import SynthOrchestrator
    print("✓ Orchestrator imported successfully")
except Exception as e:
    print(f"✗ Orchestrator import failed: {e}")
    sys.exit(1)

# Test 2: Check ProjectPhase enum
print("\n" + "=" * 60)
print("TEST 2: ProjectPhase States")
print("=" * 60)

expected_phases = ['INITIALIZATION', 'PLANNING', 'ITERATION', 'EXIT', 'PAUSED']
actual_phases = [phase.name for phase in ProjectPhase]

for phase in expected_phases:
    if phase in actual_phases:
        print(f"✓ Phase {phase} exists")
    else:
        print(f"✗ Phase {phase} missing")
        sys.exit(1)

# Test 3: Check GDIL has required methods
print("\n" + "=" * 60)
print("TEST 3: GDIL Required Methods")
print("=" * 60)

required_methods = [
    'start_project',
    'process_clarification',
    'start_iteration',
    'continue_iteration',
    'get_project_status',
    'resume_project'
]

for method_name in required_methods:
    if hasattr(GoalDirectedIterationLoop, method_name):
        print(f"✓ Method '{method_name}' exists")
    else:
        print(f"✗ Method '{method_name}' missing")
        sys.exit(1)

# Test 4: Check orchestrator integration points
print("\n" + "=" * 60)
print("TEST 4: Orchestrator Integration")
print("=" * 60)

# Read orchestrator source to check integration
orchestrator_path = Path("core/orchestrator.py")
orchestrator_code = orchestrator_path.read_text()

checks = {
    "GDIL import": "from psychological.goal_directed_iteration import GoalDirectedIterationLoop",
    "GDIL instance variable": "self.gdil: Optional[GoalDirectedIterationLoop]",
    "GDIL initialization": "self.gdil = GoalDirectedIterationLoop",
    "Project command handler": 'cmd.startswith("/project ")',
    "Project status command": 'cmd == "/project status"',
    "Resume command": 'cmd == "/resume project"',
    "Phase-based routing": "if self.gdil.active_project:",
}

for check_name, check_string in checks.items():
    if check_string in orchestrator_code:
        print(f"✓ {check_name} found")
    else:
        print(f"✗ {check_name} missing")
        sys.exit(1)

# Test 5: Configuration parameters
print("\n" + "=" * 60)
print("TEST 5: GDIL Configuration")
print("=" * 60)

# Create mock objects to test initialization
class MockLLM:
    pass

class MockMemory:
    def store_episodic(self, *args, **kwargs):
        pass

class MockEmotion:
    def apply_reward_signal(self, *args, **kwargs):
        pass
    def current_state(self):
        return {}
    def get_current_state(self):
        return {"valence": 0.5, "arousal": 0.5}

class MockTemporal:
    pass

class MockDreaming:
    pass

class MockAssurance:
    pass

class MockReflection:
    pass

class MockCalibration:
    pass

try:
    gdil = GoalDirectedIterationLoop(
        llm=MockLLM(),
        memory=MockMemory(),
        emotion_regulator=MockEmotion(),
        temporal_purpose=MockTemporal(),
        predictive_dreaming=MockDreaming(),
        assurance_module=MockAssurance(),
        meta_reflection=MockReflection(),
        reward_calibration=MockCalibration(),
        iteration_threshold=0.1,
        max_iterations=10,
        stall_iterations=3
    )
    print("✓ GDIL instance created successfully")
    print(f"  - iteration_threshold: {gdil.iteration_threshold}")
    print(f"  - max_iterations: {gdil.max_iterations}")
    print(f"  - stall_iterations: {gdil.stall_iterations}")
    print(f"  - active_project: {gdil.active_project}")
except Exception as e:
    print(f"✗ GDIL initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Project state initialization
print("\n" + "=" * 60)
print("TEST 6: Project State Management")
print("=" * 60)

# Check that project structure would be created correctly
if gdil.active_project is None:
    print("✓ No active project initially (correct)")
else:
    print("✗ Active project should be None initially")
    sys.exit(1)

if gdil.project_history == []:
    print("✓ Project history empty initially (correct)")
else:
    print("✗ Project history should be empty initially")
    sys.exit(1)

# Test 7: Check command help text updated
print("\n" + "=" * 60)
print("TEST 7: User-Facing Documentation")
print("=" * 60)

run_synth_path = Path("run_synth.py")
run_synth_code = run_synth_path.read_text()

if "/project [desc]" in run_synth_code:
    print("✓ /project command documented in banner")
else:
    print("✗ /project command not documented")
    sys.exit(1)

if "/project status" in run_synth_code:
    print("✓ /project status command documented")
else:
    print("✗ /project status command not documented")
    sys.exit(1)

if "/resume project" in run_synth_code:
    print("✓ /resume project command documented")
else:
    print("✗ /resume project command not documented")
    sys.exit(1)

# Test 8: Documentation files exist
print("\n" + "=" * 60)
print("TEST 8: Documentation Files")
print("=" * 60)

docs = {
    "GDIL_README.md": Path("GDIL_README.md"),
    "GDIL_COMPLETE.md": Path("GDIL_COMPLETE.md"),
}

for doc_name, doc_path in docs.items():
    if doc_path.exists():
        size = doc_path.stat().st_size
        lines = len(doc_path.read_text().splitlines())
        print(f"✓ {doc_name} exists ({lines} lines, {size} bytes)")
    else:
        print(f"✗ {doc_name} missing")
        sys.exit(1)

# Final summary
print("\n" + "=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print("\nGDIL Integration Status:")
print("  ✓ All imports working")
print("  ✓ All required methods present")
print("  ✓ Orchestrator integration complete")
print("  ✓ Configuration system working")
print("  ✓ Documentation complete")
print("\nNext steps:")
print("  1. Set API key: export ANTHROPIC_API_KEY='your-key'")
print("  2. Run: python run_synth.py")
print("  3. Test: /project Build a simple calculator")
print("\nNote: Full end-to-end testing requires LLM API access")
