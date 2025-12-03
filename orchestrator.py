"""
buildOS agent_system5: SDK-First Orchestrator

Orchestrator using ClaudeSDKClient to coordinate buildOS agents.
Key principle: Let the SDK handle routing, spawning, context management, and coordination.
"""

import asyncio
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx
import json

# Load environment variables if .env exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use system environment

# Import Claude SDK
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage

# Import local modules
from sdk_tools import create_ifc_tools_server
from conversation_logger import ConversationLogger


async def send_event(event_type: str, payload: dict, session_id: str, dashboard_url: str):
    """Send event to dashboard server."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{dashboard_url}/events",
                json={
                    "source_app": "buildos-orchestrator",
                    "session_id": session_id,
                    "hook_event_type": event_type,
                    "payload": payload
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"Failed to send event: {e}", file=sys.stderr)


async def stream_to_dashboard(client: ClaudeSDKClient, session_id: str, dashboard_url: str, logger: ConversationLogger):
    """
    Stream SDK events to dashboard in real-time AND log to conversation logger.

    Maps SDK message types to:
    1. Dashboard events (for real-time UI)
    2. Conversation logs (for full observability)

    Captures:
    - AssistantMessage (TextBlock) → Model thinking/reasoning
    - ToolUseBlock → Tool calls with full inputs
    - ToolResultBlock → Tool results with outputs
    - ResultMessage → Model metrics (cost, tokens, duration)
    """
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Model thinking/reasoning - LOG IT
                    logger.log_model_thinking(block.text, agent_id="orchestrator")
                    
                    # Also send to dashboard for real-time UI
                    await send_event("AgentThinking", {
                        "thought": block.text,
                        "timestamp": datetime.now().isoformat()
                    }, session_id, dashboard_url)

                elif isinstance(block, ToolUseBlock):
                    # Tool call detected - LOG FULL INPUT
                    logger.log_tool_call(
                        tool_name=block.name,
                        tool_input=block.input,
                        agent_id="orchestrator"
                    )
                    
                    if block.name == "Task":
                        # Subagent spawn - LOG IT
                        agent_type = block.input.get("subagent_type", "unknown")
                        agent_id = f"{agent_type}_{session_id[:8]}"
                        logger.log_agent_spawn(
                            agent_type=agent_type,
                            agent_id=agent_id,
                            prompt=block.input.get("description", "")
                        )
                        
                        # Send to dashboard
                        await send_event("SubagentStart", {
                            "agent_type": agent_type,
                            "agent_id": agent_id,
                            "description": block.input.get("description", ""),
                            "timestamp": datetime.now().isoformat()
                        }, session_id, dashboard_url)
                    else:
                        # Other tool use
                        await send_event("AgentThinking", {
                            "thought": f"Using tool: {block.name}",
                            "timestamp": datetime.now().isoformat()
                        }, session_id, dashboard_url)

                elif isinstance(block, ToolResultBlock):
                    # Tool result - LOG FULL OUTPUT
                    tool_result = block.content if hasattr(block, 'content') else str(block)
                    is_error = block.is_error if hasattr(block, 'is_error') else False
                    
                    logger.log_tool_result(
                        tool_name="unknown",  # SDK doesn't provide tool name in result
                        tool_output=tool_result,
                        success=not is_error,
                        error=tool_result if is_error else None,
                        agent_id="orchestrator"
                    )
                    
                    # Send to dashboard
                    await send_event("AgentThinking", {
                        "thought": "Tool execution completed",
                        "timestamp": datetime.now().isoformat()
                    }, session_id, dashboard_url)

        elif isinstance(message, ResultMessage):
            # Log model metrics
            metrics = {
                "cost_usd": message.total_cost_usd if hasattr(message, 'total_cost_usd') else None,
                "duration_ms": message.duration_ms if hasattr(message, 'duration_ms') else None,
                "num_turns": message.num_turns if hasattr(message, 'num_turns') else None,
            }
            logger.log_model_metrics(metrics, agent_id="orchestrator")
            
            # Final result with metrics
            await send_event("AgentMetrics", {
                **metrics,
                "timestamp": datetime.now().isoformat()
            }, session_id, dashboard_url)

            # Send completion event
            await send_event("Stop", {
                "status": "success" if not message.is_error else "error",
                "message": f"Analysis completed: {message.result if hasattr(message, 'result') else 'Done'}",
                "timestamp": datetime.now().isoformat()
            }, session_id, dashboard_url)


async def run_orchestrator(
    message: str,
    session_id: str,
    dashboard_url: str,
    file_path: Optional[str] = None,
    available_files: Optional[list] = None
) -> None:
    """
    Main orchestrator using ClaudeSDKClient.

    Flow:
    1. Validate file exists
    2. Setup workspace + session context
    3. Register IFC tools via MCP server
    4. Create ClaudeSDKClient with agents auto-discovered from .claude/agents/
    5. Send user message to SDK
    6. Stream responses to dashboard

    The SDK handles:
    - Agent spawning via Task tool
    - Context management
    - Tool routing based on allowed_tools
    - Error handling
    """

    # Initialize session logger
    logger = ConversationLogger(session_id)
    
    # Log user message and available context
    logger.log_user_message(message, file_path)
    logger.log_system_context({
        "file_path": file_path,
        "available_files": available_files or [],
        "dashboard_url": dashboard_url
    })

    # Send session start event
    await send_event("SessionStart", {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    }, session_id, dashboard_url)

    # Setup workspace
    workspace = Path("./workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    # Validate file if provided
    if file_path:
        ifc_path = Path(file_path)
        if not ifc_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.log_error("FileNotFound", error_msg)
            await send_event("Stop", {
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }, session_id, dashboard_url)
            print(f"ERROR: {error_msg}", file=sys.stderr)
            logger.log_session_end("error", {"reason": error_msg})
            return

        filename = ifc_path.stem

        # Create session context folder
        session_context = workspace / ".context" / f"{filename}_{session_id[:8]}"
        session_context.mkdir(parents=True, exist_ok=True)
    else:
        session_context = workspace / ".context" / f"session_{session_id[:8]}"
        session_context.mkdir(parents=True, exist_ok=True)
        filename = "unknown"

    # Send initialization event
    await send_event("AgentThinking", {
        "thought": f"Initializing buildOS orchestrator for session {session_id[:8]}",
        "timestamp": datetime.now().isoformat()
    }, session_id, dashboard_url)
    
    logger.log_debug("Orchestrator initialized", {
        "session_context": str(session_context),
        "filename": filename
    })

    # Register IFC tools as MCP server
    ifc_server = create_ifc_tools_server()
    logger.log_debug("IFC tools registered", {"server": "ifc"})

    # Configure SDK options
    options = ClaudeAgentOptions(
        mcp_servers={"ifc": ifc_server},
        allowed_tools=[
            "Task",           # Allow agent spawning
            "Read",           # File reading
            "Write",          # File writing
            "Bash",           # Command execution
            "mcp__ifc__*"     # All IFC tools
        ],
        permission_mode="bypassPermissions",  # Auto-approve for automation
        cwd=str(workspace),
        setting_sources=["project"],  # Auto-loads .claude/agents/*.md
        model="claude-sonnet-4-5"  # Orchestrator uses Sonnet
    )

    # Send agent thinking event
    await send_event("AgentThinking", {
        "thought": "SDK initialized, analyzing user request...",
        "timestamp": datetime.now().isoformat()
    }, session_id, dashboard_url)

    try:
        # SDK IS the orchestrator - it coordinates everything
        async with ClaudeSDKClient(options=options) as client:
            # Build orchestrator prompt
            orchestrator_prompt = f"""You are the buildOS orchestrator coordinating specialized agents.

**User Request**: "{message}"
**IFC File**: {file_path if file_path else "No file provided"}
**Available Files**: {', '.join(available_files) if available_files else "None"}
**Session Context Folder**: {session_context}/
**Session ID**: {session_id}

Your job is to:
1. Classify the user's intent
2. Coordinate specialized agents to fulfill the request
3. Validate agent completeness
4. Report results to the user

## Intent Classification

Classify into one of:

### Simple Query
Pattern: "How many [element type]?" or "List [element type]"
Action: Spawn single explore agent for quick answer

### Exploratory
Pattern: "What's in the model?" or "Analyze structure"
Action: Spawn explore agent with comprehensive summary

### Full CO2 Analysis
Pattern: "Calculate CO2" or "Environmental impact" or "Sustainability report"
Action: Run 4-phase workflow:
1. data-prep: Parse IFC file → create batches
2. batch-processor × N: Classify elements (parallel)
3. durability-calculator × N: Calculate CO2 (parallel)
4. pdf-report-generator: Create final PDF report

## Agent Coordination

Use the Task tool to spawn agents:
```
Task(
    subagent_type="data-prep",
    description="Parse Small_condo.ifc and create classification batches",
    model="haiku"
)
```

Available agents: data-prep, batch-processor, durability-calculator, pdf-report-generator

## Validation Loop

After each agent completes:
1. Review output files in {session_context}/
2. Check completeness:
   - data-prep: batches.json exists with all elements?
   - batch-processor: ALL elements classified?
   - calculator: ALL elements have CO2 values?
3. If incomplete: Re-spawn agent with specific feedback (max 2 retries)
4. If complete: Proceed to next phase

## IFC Tools Available

You have access to these MCP tools:
- mcp__ifc__parse_ifc_file(ifc_path, output_path) - Parse IFC to JSON
- mcp__ifc__prepare_batches(json_path, batch_size, output_path) - Create batches
- mcp__ifc__calculate_co2(classified_path, database_path, output_path) - Calculate CO2
  * database_path should be: .claude/tools/co2_factors.json

Coordinate agents efficiently and report results clearly.
"""

            # Log the orchestrator prompt - FULL VISIBILITY
            logger.log_model_prompt(
                role="system",
                content=orchestrator_prompt,
                model="claude-sonnet-4-5",
                agent_id="orchestrator"
            )
            logger.log_debug("Sending query to SDK", {"prompt_length": len(orchestrator_prompt)})

            # Send query to SDK
            await client.query(orchestrator_prompt)

            # Stream events to dashboard AND log everything
            await stream_to_dashboard(client, session_id, dashboard_url, logger)
            
            logger.log_session_end("completed", {"status": "success"})

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in orchestrator: {e}", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        
        logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=error_trace
        )

        await send_event("Stop", {
            "status": "error",
            "message": f"Orchestrator error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, session_id, dashboard_url)
        
        logger.log_session_end("error", {"error": str(e)})

    finally:
        # Send session end event
        await send_event("SessionEnd", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id, dashboard_url)


def main():
    """Parse arguments and run orchestrator."""
    parser = argparse.ArgumentParser(description="buildOS SDK-First Orchestrator")
    parser.add_argument('--message', required=True, help="User's query")
    parser.add_argument('--session-id', required=True, help="Session identifier")
    parser.add_argument('--dashboard-url', default='http://localhost:4000', help="Dashboard URL")
    parser.add_argument('--file-path', help="Path to IFC file")
    parser.add_argument('--available-files', help="JSON array of available file paths")

    args = parser.parse_args()
    
    # Parse available files if provided
    available_files = None
    if args.available_files:
        try:
            available_files = json.loads(args.available_files)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse available-files JSON", file=sys.stderr)

    try:
        asyncio.run(run_orchestrator(
            args.message,
            args.session_id,
            args.dashboard_url,
            args.file_path,
            available_files
        ))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
