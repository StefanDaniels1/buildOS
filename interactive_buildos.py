#!/usr/bin/env python3
"""
buildOS Interactive Session
Interactive conversation-based orchestrator for IFC CO2 analysis
"""

import asyncio
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


class BuildOSSession:
    """Interactive buildOS conversation session with context memory."""

    def __init__(self):
        # Setup workspace
        self.workspace = Path("./workspace")
        self.workspace.mkdir(exist_ok=True)
        
        # Register IFC tools as MCP server
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
                "Read",
                "Write",
                "Task"
            ],
            permission_mode="acceptEdits",
            cwd=str(self.workspace),
            setting_sources=["project"]  # Loads .claude/agents/
        )
        
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0
        self.current_session_context = None

    async def start(self):
        """Start interactive session."""
        await self.client.connect()
        
        print("\n" + "="*80)
        print("🏗️  buildOS Interactive Session")
        print("="*80)
        print("BIM AI CO2 Analysis System - Conversation Mode")
        print()
        print("💡 Example prompts:")
        print("   • 'Analyze Small_condo.ifc for CO2 impact'")
        print("   • 'Parse the IFC file and show me the element count'")
        print("   • 'Create batches from the parsed data'")
        print("   • 'Process batch 1 using the batch-processor agent'")
        print()
        print("⚙️  Commands:")
        print("   • 'exit' - Quit session")
        print("   • 'interrupt' - Stop current task")
        print("   • 'new' - Start fresh session (clears context)")
        print("   • 'status' - Show current workspace status")
        print()
        print("📊 Dashboard: http://localhost:5173 (watch agent activity)")
        print("="*80)
        print()
        
        while True:
            try:
                user_input = input(f"\n[Turn {self.turn_count + 1}] 💬 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting...")
                break

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() == 'exit':
                print("\n👋 Goodbye!")
                break
            
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("⚠️  Task interrupted!")
                continue
            
            elif user_input.lower() == 'new':
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                self.current_session_context = None
                print("\n✨ Started new session (context cleared)")
                continue
            
            elif user_input.lower() == 'status':
                self.show_status()
                continue

            # Send message to Claude (context remembered)
            await self.client.query(user_input)
            self.turn_count += 1

            # Process and display response
            print(f"\n[Turn {self.turn_count}] 🤖 Claude:\n")
            print("-" * 80)
            
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                        elif isinstance(block, ToolUseBlock):
                            print(f"\n🔧 Using tool: {block.name}")
                
                elif isinstance(message, ResultMessage):
                    print("\n" + "-" * 80)
                    if message.total_cost_usd:
                        print(f"💰 Cost: ${message.total_cost_usd:.4f}")
                    if message.duration_ms:
                        print(f"⏱️  Time: {message.duration_ms/1000:.1f}s")

        await self.client.disconnect()
        print(f"\n✅ Session ended after {self.turn_count} turns.")
        print(f"📁 Workspace: {self.workspace.absolute()}")

    def show_status(self):
        """Show current workspace status."""
        print("\n" + "="*80)
        print("📊 Workspace Status")
        print("="*80)
        
        # Check for session contexts
        context_dir = self.workspace / ".context"
        if context_dir.exists():
            sessions = list(context_dir.glob("*/"))
            print(f"Session contexts: {len(sessions)}")
            for session in sorted(sessions)[-3:]:  # Last 3
                print(f"  • {session.name}")
        else:
            print("Session contexts: None")
        
        # Check for output files
        batch_files = list(self.workspace.glob("batch_*.json"))
        print(f"\nBatch outputs: {len(batch_files)}")
        for batch in sorted(batch_files):
            size = batch.stat().st_size / 1024
            print(f"  • {batch.name} ({size:.1f} KB)")
        
        # Check for IFC files
        ifc_files = list(Path(".").glob("*.ifc"))
        print(f"\nIFC files: {len(ifc_files)}")
        for ifc in ifc_files[:5]:  # First 5
            print(f"  • {ifc.name}")
        
        print("="*80)


async def main():
    """Main entry point."""
    session = BuildOSSession()
    await session.start()


if __name__ == "__main__":
    asyncio.run(main())
