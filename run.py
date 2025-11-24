"""
BIM AI CO2 Analysis - Simplified Orchestrator

This is the main entry point. Run with:
    uv run python run.py Small_condo.ifc

Or for interactive mode:
    uv run python run.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage
)

from tools.ifc_analysis_tool import (
    parse_ifc_file,
    get_geometric_elements,
    prepare_classification_batches,
    classify_elements,
    aggregate_classifications
)


async def run_analysis(ifc_file: str):
    """
    Run CO2 analysis on an IFC file.

    This function creates a Claude session with all necessary tools
    and lets Claude orchestrate the entire workflow autonomously.
    """

    # Validate input
    if not Path(ifc_file).exists():
        print(f"❌ Error: File not found: {ifc_file}")
        return

    # Create workspace and session context folders
    workspace = Path("./workspace")
    workspace.mkdir(exist_ok=True)

    # Create session context folder with timestamp
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    ifc_basename = Path(ifc_file).stem
    session_context = workspace / ".context" / f"{ifc_basename}_{session_id}"
    session_context.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("BIM AI CO2 ANALYSIS")
    print("="*80)
    print(f"IFC File: {ifc_file}")
    print(f"Workspace: {workspace.absolute()}")
    print(f"Session Context: {session_context.relative_to(workspace)}")
    print("="*80)

    # Register tools as MCP server
    ifc_server = create_sdk_mcp_server(
        name="ifc-analysis",
        version="1.0.0",
        tools=[
            parse_ifc_file,
            get_geometric_elements,
            prepare_classification_batches,
            classify_elements,
            aggregate_classifications
        ]
    )

    # Configure Claude with tools and agents
    options = ClaudeAgentOptions(
        mcp_servers={"ifc": ifc_server},
        allowed_tools=[
            "mcp__ifc__parse_ifc_file",
            "mcp__ifc__prepare_classification_batches",
            "Task"  # Only need Task tool to spawn batch-processor agent
        ],
        permission_mode="acceptEdits",
        cwd=str(workspace),
        setting_sources=["project"]  # Loads .claude/agents/ (batch-processor.md)
    )

    # Start Claude session
    async with ClaudeSDKClient(options=options) as client:

        # Give Claude the goal, let it figure out the steps
        ifc_abs_path = str(Path(ifc_file).absolute())
        session_context_rel = str(session_context.relative_to(workspace))

        await client.query(
            f"""Analyze the IFC file for CO2 impact assessment.

**CRITICAL RULES:**
1. Execute each tool call EXACTLY ONCE - never repeat
2. Wait for each tool to complete before proceeding to next step
3. Use exact file paths as specified
4. Report progress to user between steps

**FILE PATHS:**
- IFC file (absolute): {ifc_abs_path}
- Working directory: {workspace.absolute()}
- Session context folder: {session_context_rel}/
- Output files location: workspace root (your CWD)

**WORKFLOW - Execute Once Per Step:**

## Step 1: Parse IFC File
Call `mcp__ifc__parse_ifc_file` with:
```
ifc_path: "{ifc_abs_path}"
output_path: "{session_context_rel}/parsed_data.json"
include_validation: true
```
After completion, report: "✓ IFC parsing complete. Found X geometric elements."

## Step 2: Prepare Batches
Call `mcp__ifc__prepare_classification_batches` with:
```
json_path: "{session_context_rel}/parsed_data.json"
batch_size: 50
output_path: "{session_context_rel}/batches.json"
```
After completion, report: "✓ Created X batches for parallel processing."

## Step 3: Process Batch 1
Report to user: "✓ Starting batch 1 classification (50 elements)..."

Call `Task` tool with:
```
subagent_type: "batch-processor"
model: "haiku"
prompt: "Process batch 1 for sustainability analysis.

**Input:**
- Session context: {session_context_rel}/
- Batch file: {session_context_rel}/batches.json
- Batch number: 1 (extract batches[0])
- Output file: batch_1_elements.json (workspace root)

**Your task:**
1. Read {session_context_rel}/batches.json
2. Extract batches[0] (first batch)
3. Process ALL elements in that batch (should be ~50 elements)
4. For each element, extract complete structured data:
   - Element identity (global_id, ifc_type, name, element_type)
   - Function classification (function, structural_role, location)
   - Materials (material_primary, material_secondary, material_notes)
   - Quantities (volume_m3, area_m2, dimensions)
   - Properties & context (properties, spatial_context)
   - Quality assessment (confidence, data_quality, reasoning)
5. Write output to batch_1_elements.json (workspace root)
6. Verify output count matches input count

**CRITICAL**: Process EVERY element. If batch has 50 elements, output must have 50.

Work efficiently. Target: 30-60 seconds for 50 elements."
```

Wait for agent to complete.

## Step 4: Verify and Report Results
After agent completes:
1. Read `batch_1_elements.json`
2. Parse the JSON array
3. Calculate and report:
   - Total elements classified
   - Element type breakdown (e.g., "20 columns, 15 walls, 10 slabs, 5 beams")
   - Material category summary (e.g., "35 concrete, 10 steel, 5 timber")
   - Average confidence score
   - Data completeness metrics
4. Report: "✓ Classification complete! Processed X elements. Output: batch_1_elements.json"

**TROUBLESHOOTING:**
- If a tool fails, report the error and STOP (do not retry)
- If output file is missing, report issue to user
- If element count doesn't match, flag the discrepancy
"""
        )

        # Collect and display response
        print("\n🤖 Claude is working...\n")
        print("-"*80)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n  🔧 Tool: {block.name}")

            elif isinstance(message, ResultMessage):
                print("\n" + "-"*80)
                if message.total_cost_usd:
                    print(f"💰 Cost: ${message.total_cost_usd:.4f}")
                if message.duration_ms:
                    print(f"⏱️  Time: {message.duration_ms/1000:.1f}s")

        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        print(f"📁 Final outputs: {workspace}/")
        print(f"📂 Session context: {session_context.relative_to(workspace)}/")


async def interactive_mode():
    """
    Interactive mode - chat with Claude about BIM analysis.
    """

    workspace = Path("./workspace")
    workspace.mkdir(exist_ok=True)

    # Create a shared context folder for interactive sessions
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_context = workspace / ".context" / f"interactive_{session_id}"
    session_context.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("BIM AI CO2 ANALYSIS - INTERACTIVE MODE")
    print("="*80)
    print("Type your requests or 'quit' to exit")
    print(f"Session context: {session_context.relative_to(workspace)}")
    print("="*80)

    # Register tools
    ifc_server = create_sdk_mcp_server(
        name="ifc-analysis",
        version="1.0.0",
        tools=[
            parse_ifc_file,
            get_geometric_elements,
            prepare_classification_batches,
            classify_elements,
            aggregate_classifications
        ]
    )

    options = ClaudeAgentOptions(
        mcp_servers={"ifc": ifc_server},
        allowed_tools=[
            "mcp__ifc__parse_ifc_file",
            "mcp__ifc__get_geometric_elements",
            "mcp__ifc__prepare_classification_batches",
            "mcp__ifc__classify_elements",
            "mcp__ifc__aggregate_classifications",
            "Read",
            "Write",
            "Task"
        ],
        permission_mode="acceptEdits",
        cwd=str(workspace),
        setting_sources=["project"]
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input or user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            await client.query(user_input)

            print("\n🤖 Claude:")
            print("-"*80)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                        elif isinstance(block, ToolUseBlock):
                            print(f"\n  🔧 {block.name}")

                elif isinstance(message, ResultMessage):
                    if message.total_cost_usd:
                        print(f"\n💰 ${message.total_cost_usd:.4f}")


async def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        # File analysis mode
        ifc_file = sys.argv[1]
        await run_analysis(ifc_file)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
