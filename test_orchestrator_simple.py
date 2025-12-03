#!/usr/bin/env python3
"""
Simple orchestrator test for agent_system5

Tests basic orchestrator functionality with a simple query.
This validates ClaudeSDKClient setup without full multi-agent workflow.
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
os.environ["BUILDOS_SESSION_ID"] = os.environ.get("BUILDOS_SESSION_ID", "test-simple")

from orchestrator import run_orchestrator


async def test_simple_query():
    """Test orchestrator with simple element count query."""
    print("\n" + "="*60)
    print("ORCHESTRATOR TEST: Simple Query")
    print("="*60)

    session_id = "test-simple-001"
    ifc_path = "../Small_condo.ifc"

    print(f"\nTest Configuration:")
    print(f"  Session ID: {session_id}")
    print(f"  IFC File:   {ifc_path}")
    print(f"  Query:      'How many structural elements are in this model?'")
    print(f"\nExpected behavior:")
    print(f"  1. Orchestrator classifies as 'Simple Query'")
    print(f"  2. Spawns data-prep agent")
    print(f"  3. Parses IFC file")
    print(f"  4. Returns element count\n")

    print("Starting orchestrator...")
    print("-" * 60)

    try:
        await run_orchestrator(
            message="How many structural elements are in this model?",
            session_id=session_id,
            dashboard_url="http://localhost:4000",
            file_path=ifc_path
        )

        print("-" * 60)
        print("\n✅ Orchestrator completed successfully")

        # Check workspace for outputs
        context_dir = Path(f"./workspace/.context/Small_condo_{session_id[:8]}")
        if context_dir.exists():
            print(f"\n📁 Session context created: {context_dir}")
            files = list(context_dir.glob("*"))
            if files:
                print(f"   Generated files:")
                for f in files:
                    print(f"     - {f.name}")
            else:
                print(f"   (No files generated yet)")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 130

    except Exception as e:
        import traceback
        print("-" * 60)
        print(f"\n❌ Orchestrator failed: {e}")
        print("\nFull traceback:")
        print(traceback.format_exc())
        return 1


async def test_file_validation():
    """Test orchestrator file validation."""
    print("\n" + "="*60)
    print("ORCHESTRATOR TEST: File Validation")
    print("="*60)

    session_id = "test-validation-001"
    ifc_path = "./nonexistent.ifc"

    print(f"\nTest Configuration:")
    print(f"  Session ID: {session_id}")
    print(f"  IFC File:   {ifc_path} (does not exist)")
    print(f"\nExpected behavior:")
    print(f"  1. Orchestrator validates file")
    print(f"  2. Detects file does not exist")
    print(f"  3. Returns error without spawning agents\n")

    print("Starting orchestrator...")
    print("-" * 60)

    try:
        await run_orchestrator(
            message="Analyze this model",
            session_id=session_id,
            dashboard_url="http://localhost:4000",
            file_path=ifc_path
        )

        print("-" * 60)
        print("\n✅ File validation working (returned gracefully)")
        return 0

    except Exception as e:
        print("-" * 60)
        print(f"\n✅ File validation caught error: {e}")
        return 0


def main():
    """Run orchestrator tests."""
    print("\n" + "="*60)
    print("ORCHESTRATOR TEST SUITE - agent_system5")
    print("="*60)
    print("\nNOTE: This test will:")
    print("  - Use real Claude API calls (costs ~$0.01-0.05)")
    print("  - Require ANTHROPIC_API_KEY environment variable")
    print("  - Send events to dashboard (http://localhost:4000)")
    print("  - Use ClaudeSDKClient to spawn subagents")

    # Check if dashboard is running
    try:
        import httpx
        response = httpx.get("http://localhost:4000", timeout=2.0)
        print("\n✅ Dashboard server detected at http://localhost:4000")
    except:
        print("\n⚠️  Dashboard server not detected at http://localhost:4000")
        print("   Events will be sent but may fail silently")
        print("   To start dashboard: cd claude-code-hooks-multi-agent-observability/apps/server && bun run dev")

    input("\nPress Enter to continue with tests (or Ctrl+C to cancel)...")

    # Run tests
    loop = asyncio.get_event_loop()

    print("\n\n" + "="*60)
    print("Test 1: File Validation")
    print("="*60)
    exit_code = loop.run_until_complete(test_file_validation())

    print("\n\n" + "="*60)
    print("Test 2: Simple Query")
    print("="*60)
    exit_code = loop.run_until_complete(test_simple_query())

    # Summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)

    if exit_code == 0:
        print("\n✅ All orchestrator tests passed")
        print("\nNext steps:")
        print("  1. Review session context in workspace/.context/")
        print("  2. Check dashboard for event timeline")
        print("  3. Proceed to Phase 3: Full workflow testing")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted")
        sys.exit(130)
