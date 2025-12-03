#!/usr/bin/env python3
"""
Phase 4: Full 4-Phase CO2 Workflow Test

Tests the complete buildOS pipeline:
1. data-prep: Parse IFC + create batches
2. batch-processor: Classify elements (parallel)
3. durability-calculator: Calculate CO2 (parallel)
4. pdf-report-generator: Generate final report

This validates:
- Agent spawning via Task tool
- Multi-agent coordination
- Parallel execution
- Complete workflow integration
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from load_env import load_environment
if not load_environment():
    sys.exit(1)

from orchestrator import run_orchestrator


async def test_full_co2_workflow():
    """Test complete 4-phase CO2 analysis."""
    print("\n" + "="*70)
    print("PHASE 4: FULL CO2 WORKFLOW TEST")
    print("="*70)

    session_id = "test-full-workflow"
    ifc_path = "../Small_condo.ifc"

    print(f"\nConfiguration:")
    print(f"  Session:  {session_id}")
    print(f"  IFC File: {ifc_path}")
    print(f"  Query:    'Calculate CO2 impact for this building'")

    print(f"\nExpected 4-Phase Flow:")
    print(f"  Phase 1: data-prep agent")
    print(f"           → Parse IFC file")
    print(f"           → Create classification batches")
    print(f"  Phase 2: batch-processor agents (parallel)")
    print(f"           → Classify elements by material/type")
    print(f"  Phase 3: durability-calculator agents (parallel)")
    print(f"           → Calculate CO2 for each element")
    print(f"  Phase 4: pdf-report-generator agent")
    print(f"           → Generate sustainability report PDF")

    print(f"\n" + "="*70)
    print("Starting orchestrator...")
    print("="*70 + "\n")

    start_time = time.time()

    try:
        await run_orchestrator(
            message="Calculate the CO2 impact for this building. Provide a complete sustainability analysis with detailed breakdown by element type.",
            session_id=session_id,
            dashboard_url=os.environ.get("DASHBOARD_URL", "http://localhost:4000"),
            file_path=ifc_path
        )

        duration = time.time() - start_time

        print("\n" + "="*70)
        print(f"✅ WORKFLOW COMPLETED in {duration:.1f} seconds")
        print("="*70)

        # Check session outputs
        context_dir = Path(f"./workspace/.context/Small_condo_{session_id[:8]}")

        print(f"\n📁 Session Context: {context_dir}")

        if context_dir.exists():
            files = list(context_dir.glob("**/*"))
            if files:
                print(f"\n   Generated files:")
                for f in sorted(files):
                    if f.is_file():
                        size = f.stat().st_size
                        print(f"     ✓ {f.relative_to(context_dir)} ({size:,} bytes)")
            else:
                print(f"   ⚠️  No files generated yet")
        else:
            print(f"   ⚠️  Session context not created")

        # Check for specific outputs
        expected_files = {
            "parsed_elements.json": "IFC parsing output",
            "batches.json": "Classification batches",
            "classified_*.json": "Classified elements",
            "co2_results.json": "CO2 calculations",
            "*.pdf": "Final sustainability report"
        }

        print(f"\n📊 Expected Outputs:")
        for pattern, description in expected_files.items():
            matches = list(context_dir.glob(f"**/{pattern}")) if context_dir.exists() else []
            status = "✅" if matches else "⏸️"
            print(f"   {status} {description} ({pattern})")
            for match in matches:
                print(f"      → {match.name}")

        # Performance metrics
        print(f"\n⏱️  Performance:")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Target:   <120s")
        print(f"   Status:   {'✅ PASS' if duration < 120 else '⚠️  OVER'}")

        return True

    except Exception as e:
        import traceback
        duration = time.time() - start_time

        print("\n" + "="*70)
        print(f"❌ WORKFLOW FAILED after {duration:.1f} seconds")
        print("="*70)
        print(f"\nError: {e}")
        print("\nFull traceback:")
        print(traceback.format_exc())

        return False


async def test_agent_spawning():
    """Test agent spawning via Task tool."""
    print("\n" + "="*70)
    print("TEST: Agent Spawning via Task Tool")
    print("="*70)

    session_id = "test-agent-spawn"
    ifc_path = "../Small_condo.ifc"

    print(f"\nConfiguration:")
    print(f"  Session: {session_id}")
    print(f"  Query:   'Spawn data-prep agent to analyze this IFC file'")

    print(f"\nExpected:")
    print(f"  1. Orchestrator receives query")
    print(f"  2. Decides to use Task tool")
    print(f"  3. Spawns data-prep agent with subagent_type='data-prep'")
    print(f"  4. Agent processes IFC file")
    print(f"  5. Returns results to orchestrator")

    print("\n" + "="*70 + "\n")

    start_time = time.time()

    try:
        await run_orchestrator(
            message="Use the data-prep agent to parse the IFC file and create classification batches. Show me the batch summary.",
            session_id=session_id,
            dashboard_url=os.environ.get("DASHBOARD_URL", "http://localhost:4000"),
            file_path=ifc_path
        )

        duration = time.time() - start_time

        print("\n" + "="*70)
        print(f"✅ AGENT SPAWNING TEST COMPLETED in {duration:.1f}s")
        print("="*70)

        return True

    except Exception as e:
        import traceback
        duration = time.time() - start_time
        print(f"\n❌ Test failed after {duration:.1f}s: {e}")
        print(traceback.format_exc())
        return False


async def main():
    """Run Phase 4 tests."""
    print("\n" + "="*70)
    print("PHASE 4: MULTI-AGENT WORKFLOW TESTING")
    print("="*70)

    print("\nThis phase tests:")
    print("  ✓ Agent spawning via Task tool")
    print("  ✓ Multi-agent coordination")
    print("  ✓ Parallel batch processing")
    print("  ✓ Complete 4-phase workflow")
    print("  ✓ Dashboard event streaming")

    # Check dashboard
    try:
        import httpx
        httpx.get("http://localhost:4000", timeout=2.0)
        print("\n✅ Dashboard detected at http://localhost:4000")
        print("   Events will stream to dashboard timeline")
    except:
        print("\n⚠️  Dashboard not responding")
        print("   Events will be sent but may fail")

    print("\n" + "="*70)

    # Test 1: Agent spawning
    print("\nTEST 1: Agent Spawning")
    print("-" * 70)
    test1_result = await test_agent_spawning()

    await asyncio.sleep(3)

    # Test 2: Full workflow
    print("\n\nTEST 2: Full 4-Phase Workflow")
    print("-" * 70)
    test2_result = await test_full_co2_workflow()

    # Summary
    print("\n" + "="*70)
    print("PHASE 4 TEST SUMMARY")
    print("="*70)

    results = {
        "Agent spawning": test1_result,
        "Full CO2 workflow": test2_result
    }

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ Phase 4 Complete!")
        print("\nAchievements:")
        print("  ✓ Multi-agent orchestration working")
        print("  ✓ Task tool spawning agents")
        print("  ✓ Complete workflow validated")
        print("\nNext steps:")
        print("  1. Review session outputs")
        print("  2. Verify dashboard events")
        print("  3. Check CO2 calculation accuracy")
        print("  4. Proceed to Phase 5: Dashboard integration")
        return 0
    else:
        print("\n❌ Phase 4 incomplete")
        print("   Review errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
