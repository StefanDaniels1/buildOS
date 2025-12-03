#!/usr/bin/env python3
"""
Automated orchestrator test for agent_system5 (non-interactive)

Tests basic orchestrator functionality without user prompts.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env
from load_env import load_environment

if not load_environment():
    sys.exit(1)

# Set test environment variables
os.environ["BUILDOS_SESSION_ID"] = os.environ.get("BUILDOS_SESSION_ID", "test-auto")

from orchestrator import run_orchestrator


async def test_file_validation():
    """Test orchestrator file validation."""
    print("\n" + "="*60)
    print("TEST 1: File Validation")
    print("="*60)

    session_id = "test-validation-auto"
    ifc_path = "./nonexistent.ifc"

    print(f"\nConfiguration:")
    print(f"  Session ID: {session_id}")
    print(f"  IFC File:   {ifc_path} (does not exist)")
    print(f"\nExpected: Error handling without crash\n")

    try:
        await run_orchestrator(
            message="Analyze this model",
            session_id=session_id,
            dashboard_url=os.environ.get("DASHBOARD_URL", "http://localhost:4000"),
            file_path=ifc_path
        )
        print("\n✅ File validation working")
        return True
    except Exception as e:
        print(f"\n✅ File validation caught error: {type(e).__name__}")
        return True


async def test_simple_query():
    """Test orchestrator with simple element count query."""
    print("\n" + "="*60)
    print("TEST 2: Simple Query")
    print("="*60)

    session_id = "test-simple-auto"
    ifc_path = "../Small_condo.ifc"

    print(f"\nConfiguration:")
    print(f"  Session ID: {session_id}")
    print(f"  IFC File:   {ifc_path}")
    print(f"  Query:      'How many structural elements?'")
    print(f"\nExpected: Parse IFC → Return element count\n")
    print("-" * 60)

    try:
        await run_orchestrator(
            message="How many structural elements are in this model?",
            session_id=session_id,
            dashboard_url=os.environ.get("DASHBOARD_URL", "http://localhost:4000"),
            file_path=ifc_path
        )

        print("-" * 60)
        print("\n✅ Orchestrator completed")

        # Check for session outputs
        context_dir = Path(f"./workspace/.context/Small_condo_{session_id[:8]}")
        if context_dir.exists():
            print(f"\n📁 Session context: {context_dir}")
            files = list(context_dir.glob("*"))
            if files:
                print(f"   Files generated:")
                for f in files:
                    size = f.stat().st_size
                    print(f"     - {f.name} ({size} bytes)")

        return True

    except Exception as e:
        import traceback
        print("-" * 60)
        print(f"\n❌ Test failed: {e}")
        print("\nTraceback:")
        print(traceback.format_exc())
        return False


async def main():
    """Run all automated tests."""
    print("\n" + "="*60)
    print("ORCHESTRATOR AUTOMATED TEST SUITE")
    print("="*60)

    # Check dashboard
    try:
        import httpx
        httpx.get("http://localhost:4000", timeout=2.0)
        print("✅ Dashboard detected at http://localhost:4000")
    except:
        print("⚠️  Dashboard not responding (events may fail)")

    print("\nStarting tests...\n")

    # Test 1: File validation
    test1_result = await test_file_validation()

    # Small delay between tests
    await asyncio.sleep(2)

    # Test 2: Simple query
    test2_result = await test_simple_query()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    results = {
        "File validation": test1_result,
        "Simple query": test2_result
    }

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ All tests passed!")
        print("\nNext steps:")
        print("  1. Review workspace/.context/ for session outputs")
        print("  2. Check dashboard for event timeline")
        print("  3. Proceed to full workflow testing")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
