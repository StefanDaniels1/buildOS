#!/usr/bin/env python3
"""
Verbose orchestrator test - shows SDK streaming output
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from load_env import load_environment
if not load_environment():
    sys.exit(1)

# Set environment
os.environ["BUILDOS_SESSION_ID"] = "test-verbose"

# Import SDK components
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage
from sdk_tools import create_ifc_tools_server


async def test_minimal_orchestrator():
    """Minimal test to verify SDK works."""
    print("\n" + "="*60)
    print("MINIMAL ORCHESTRATOR TEST")
    print("="*60)

    session_id = "test-minimal"
    ifc_path = "../Small_condo.ifc"

    print(f"\nSetup:")
    print(f"  Session: {session_id}")
    print(f"  IFC:     {ifc_path}")
    print(f"\nInitializing SDK...\n")

    # Setup workspace
    workspace = Path("./workspace")
    workspace.mkdir(exist_ok=True)

    # Register IFC tools
    ifc_server = create_ifc_tools_server()

    # Configure SDK
    options = ClaudeAgentOptions(
        mcp_servers={"ifc": ifc_server},
        allowed_tools=["Task", "Read", "Write", "Bash", "mcp__ifc__*"],
        permission_mode="bypassPermissions",
        cwd=str(workspace),
        setting_sources=["project"],
        model="claude-sonnet-4-5"
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            print("✅ SDK client created\n")

            # Simple query
            query = f"""You are a BIM analysis assistant.

IFC File: {ifc_path}

Task: Parse the IFC file and tell me how many structural elements it contains.

Use the mcp__ifc__parse_ifc_file tool to parse the file.
Output path: workspace/parsed_test.json

Report back the total count of elements found.
"""

            print("Sending query to SDK...")
            print("-" * 60)

            await client.query(query)

            print("\nStreaming SDK responses:")
            print("-" * 60)

            response_count = 0
            text_blocks = []
            tool_uses = []

            async for message in client.receive_response():
                response_count += 1
                print(f"\n[Response {response_count}] {type(message).__name__}")

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_blocks.append(block.text)
                            print(f"  TEXT: {block.text[:200]}...")

                        elif isinstance(block, ToolUseBlock):
                            tool_uses.append(block.name)
                            print(f"  TOOL: {block.name}")
                            print(f"    Input: {block.input}")

                        elif isinstance(block, ToolResultBlock):
                            print(f"  TOOL RESULT:")
                            result_preview = str(block)[:200]
                            print(f"    {result_preview}...")

                elif isinstance(message, ResultMessage):
                    print(f"\n[Final Result]")
                    if hasattr(message, 'total_cost_usd'):
                        print(f"  Cost: ${message.total_cost_usd:.4f}")
                    if hasattr(message, 'duration_ms'):
                        print(f"  Duration: {message.duration_ms}ms")
                    if hasattr(message, 'num_turns'):
                        print(f"  Turns: {message.num_turns}")

            print("\n" + "-" * 60)
            print(f"\n✅ Completed:")
            print(f"  Total responses: {response_count}")
            print(f"  Text blocks: {len(text_blocks)}")
            print(f"  Tools used: {tool_uses}")

            # Check outputs
            output_file = workspace / "parsed_test.json"
            if output_file.exists():
                import json
                with open(output_file) as f:
                    data = json.load(f)
                    print(f"\n📊 Parsed {data.get('total_count', 0)} elements")
                    return True
            else:
                print(f"\n⚠️  Output file not created: {output_file}")
                return False

    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    result = asyncio.run(test_minimal_orchestrator())
    sys.exit(0 if result else 1)
