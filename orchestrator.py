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


def load_conversation_history(session_id: str) -> list:
    """
    Load conversation history for a session to enable context continuity.
    
    Returns a list of (role, content) tuples representing the conversation.
    """
    try:
        events = ConversationLogger.load_session(session_id)
        
        history = []
        for event in events:
            event_type = event.get("event", "")
            
            # User messages
            if event_type == "user_message":
                history.append({
                    "role": "user",
                    "content": event.get("message", "")
                })
            
            # Model thinking/responses  
            elif event_type == "model_thinking":
                history.append({
                    "role": "assistant",
                    "content": event.get("content", "")
                })
            
            # Final assistant responses
            elif event_type == "assistant_message":
                history.append({
                    "role": "assistant", 
                    "content": event.get("message", "")
                })
        
        return history
    except Exception as e:
        print(f"Warning: Could not load conversation history: {e}", file=sys.stderr)
        return []


def format_conversation_context(history: list) -> str:
    """
    Format conversation history as context for the model.
    
    Returns a formatted string summarizing previous exchanges.
    """
    if not history:
        return ""
    
    context_parts = ["## Previous Conversation in This Session\n"]
    
    for i, exchange in enumerate(history):
        role = exchange.get("role", "unknown")
        content = exchange.get("content", "")
        
        # Truncate very long content
        if len(content) > 500:
            content = content[:500] + "... [truncated]"
        
        if role == "user":
            context_parts.append(f"**User**: {content}")
        elif role == "assistant":
            context_parts.append(f"**Assistant**: {content}")
    
    context_parts.append("\n---\n")
    return "\n".join(context_parts)


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


def _get_tool_description(tool_name: str, tool_input: dict) -> str:
    """Extract meaningful description from tool input for dashboard display."""

    # Bash tool - use description field or command summary
    if tool_name == "Bash":
        if tool_input.get("description"):
            return tool_input["description"]
        command = tool_input.get("command", "")
        # Truncate long commands
        if len(command) > 80:
            command = command[:77] + "..."
        return f"Running: {command}"

    # Read tool - show file path
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        # Show just filename for cleaner display
        filename = Path(file_path).name if file_path else "file"
        return f"Reading: {filename}"

    # Write tool - show file path
    if tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        filename = Path(file_path).name if file_path else "file"
        return f"Writing: {filename}"

    # Edit tool - show file and action
    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        filename = Path(file_path).name if file_path else "file"
        return f"Editing: {filename}"

    # Glob tool - show pattern
    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"Searching files: {pattern}"

    # Grep tool - show pattern
    if tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"Searching content: {pattern}"

    # MCP IFC tools - extract meaningful info
    if tool_name.startswith("mcp__ifc__"):
        action = tool_name.replace("mcp__ifc__", "").replace("_", " ").title()
        if "ifc_path" in tool_input:
            filename = Path(tool_input["ifc_path"]).name
            return f"{action}: {filename}"
        if "json_path" in tool_input:
            filename = Path(tool_input["json_path"]).name
            return f"{action}: {filename}"
        return action

    # Default - just show tool name
    return f"Using tool: {tool_name}"


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
    # Track the last text response for the final Stop event
    last_text_response = ""

    # Track pending Task calls to match with results and send SubagentEnd
    pending_tasks = {}  # tool_use_id -> {"agent_type", "agent_id", "description", "is_background"}

    # Track which agent is currently "active" (for synchronous tasks only)
    # Background tasks don't change the active agent
    active_agent_id = "orchestrator"

    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Use the active agent (only changes for synchronous tasks)
                    current_agent_id = active_agent_id

                    # Model thinking/reasoning - LOG IT
                    logger.log_model_thinking(block.text, agent_id=current_agent_id)

                    # Track this as the last text response
                    last_text_response = block.text

                    # Also send to dashboard for real-time UI
                    await send_event("AgentThinking", {
                        "thought": block.text,
                        "agent_id": current_agent_id,
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
                        agent_id = f"{agent_type}_{session_id[:8]}_{len(pending_tasks)}"
                        description = block.input.get("description", "")
                        is_background = block.input.get("run_in_background", False)

                        logger.log_agent_spawn(
                            agent_type=agent_type,
                            agent_id=agent_id,
                            prompt=description
                        )

                        # Track this pending Task to match with result later
                        tool_use_id = block.id if hasattr(block, 'id') else f"task_{len(pending_tasks)}"
                        pending_tasks[tool_use_id] = {
                            "agent_type": agent_type,
                            "agent_id": agent_id,
                            "description": description,
                            "start_time": datetime.now().isoformat(),
                            "is_background": is_background
                        }

                        # Only change active agent for synchronous (non-background) tasks
                        # Background tasks run in parallel and don't take over the main flow
                        if not is_background:
                            active_agent_id = agent_id

                        # Send to dashboard
                        await send_event("SubagentStart", {
                            "agent_type": agent_type,
                            "agent_id": agent_id,
                            "description": description,
                            "is_background": is_background,
                            "timestamp": datetime.now().isoformat()
                        }, session_id, dashboard_url)
                    else:
                        # Other tool use - extract meaningful description
                        tool_input = block.input or {}
                        thought = _get_tool_description(block.name, tool_input)

                        # Use active agent (orchestrator for background tasks, subagent for sync tasks)
                        await send_event("AgentThinking", {
                            "thought": thought,
                            "agent_id": active_agent_id,
                            "timestamp": datetime.now().isoformat()
                        }, session_id, dashboard_url)

                elif isinstance(block, ToolResultBlock):
                    # Tool result - LOG FULL OUTPUT
                    tool_result = block.content if hasattr(block, 'content') else str(block)
                    is_error = block.is_error if hasattr(block, 'is_error') else False

                    # Check if this result is for a pending Task (subagent completion)
                    tool_use_id = block.tool_use_id if hasattr(block, 'tool_use_id') else None
                    task_info = None

                    if tool_use_id and tool_use_id in pending_tasks:
                        task_info = pending_tasks.pop(tool_use_id)
                    elif pending_tasks:
                        # Fallback: match with oldest pending task (FIFO)
                        oldest_id = next(iter(pending_tasks))
                        task_info = pending_tasks.pop(oldest_id)

                    if task_info:
                        # This is a Task completion - send SubagentEnd!
                        result_summary = str(tool_result)[:200] if len(str(tool_result)) > 200 else str(tool_result)

                        logger.log_agent_response(
                            agent_id=task_info["agent_id"],
                            response=result_summary
                        )

                        await send_event("SubagentEnd", {
                            "agent_type": task_info["agent_type"],
                            "agent_id": task_info["agent_id"],
                            "description": task_info["description"],
                            "result": result_summary,
                            "success": not is_error,
                            "timestamp": datetime.now().isoformat()
                        }, session_id, dashboard_url)

                        logger.log_tool_result(
                            tool_name="Task",
                            tool_output=result_summary,
                            success=not is_error,
                            error=result_summary if is_error else None,
                            agent_id=task_info["agent_id"]
                        )

                        # Reset active agent to orchestrator when a synchronous task completes
                        if not task_info.get("is_background", False) and active_agent_id == task_info["agent_id"]:
                            active_agent_id = "orchestrator"
                    else:
                        # Regular tool result (not a Task)
                        logger.log_tool_result(
                            tool_name="unknown",
                            tool_output=tool_result,
                            success=not is_error,
                            error=tool_result if is_error else None,
                            agent_id="orchestrator"
                        )

                    # Send error results to dashboard
                    if is_error:
                        error_msg = str(tool_result)[:200] if len(str(tool_result)) > 200 else str(tool_result)
                        await send_event("AgentThinking", {
                            "thought": f"Error: {error_msg}",
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

            # Use the last text response which contains the final answer with file paths
            # Fall back to message.result if no text response was captured
            final_message = last_text_response if last_text_response else (
                message.result if hasattr(message, 'result') else 'Done'
            )

            # Send completion event with the full final response
            await send_event("Stop", {
                "status": "success" if not message.is_error else "error",
                "message": final_message,
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
    3. Load conversation history for session continuity
    4. Register IFC tools via MCP server
    5. Create ClaudeSDKClient with agents auto-discovered from .claude/agents/
    6. Send user message to SDK with history context
    7. Stream responses to dashboard

    The SDK handles:
    - Agent spawning via Task tool
    - Context management
    - Tool routing based on allowed_tools
    - Error handling
    """

    # Initialize session logger
    logger = ConversationLogger(session_id)
    
    # Load previous conversation history for this session
    conversation_history = load_conversation_history(session_id)
    is_continuation = len(conversation_history) > 0
    
    if is_continuation:
        print(f"📚 Continuing session {session_id[:8]} with {len(conversation_history)} previous exchanges", file=sys.stderr)
    else:
        print(f"🆕 Starting new session {session_id[:8]}", file=sys.stderr)
    
    # Log user message and available context
    logger.log_user_message(message, file_path)
    logger.log_system_context({
        "file_path": file_path,
        "available_files": available_files or [],
        "dashboard_url": dashboard_url,
        "is_continuation": is_continuation,
        "previous_exchanges": len(conversation_history)
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

        # Get user_id for session isolation (from environment, set by server)
        user_id = os.environ.get('BUILDOS_USER_ID', '')

        # Create session context folder with user isolation
        # Structure: .context/{user_id}/session_{unique_part}/
        unique_part = session_id.split('_', 1)[1] if '_' in session_id else session_id[:16]

        if user_id:
            # User-isolated path: .context/{user_id}/session_{timestamp}/
            session_context = workspace / ".context" / user_id / f"session_{unique_part[:12]}"
        else:
            # Fallback for local dev without user_id
            session_context = workspace / ".context" / f"{filename}_{unique_part[:12]}"

        session_context.mkdir(parents=True, exist_ok=True)
    else:
        # Get user_id for session isolation
        user_id = os.environ.get('BUILDOS_USER_ID', '')

        # Extract unique part for session-based context
        unique_part = session_id.split('_', 1)[1] if '_' in session_id else session_id[:16]

        if user_id:
            # User-isolated path
            session_context = workspace / ".context" / user_id / f"session_{unique_part[:12]}"
        else:
            # Fallback
            session_context = workspace / ".context" / f"session_{unique_part[:12]}"

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
            "mcp__ifc__*"     # All IFC tools (including Excel/PPTX generation)
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
            # Build orchestrator prompt - delegates to skill for workflow
            skill_path = "$CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/SKILL.md"

            # Format conversation history if this is a continuation
            conversation_context = format_conversation_context(conversation_history)
            continuation_note = ""
            if is_continuation:
                continuation_note = f"""
## ⚠️ IMPORTANT: This is a Continuation of Session {session_id[:8]}

You are continuing a conversation. The user has already interacted with you in this session.
Review the previous exchanges below and maintain context. Do not repeat work already done.
If the user is asking a follow-up question, answer based on the work already completed.

{conversation_context}
"""

            orchestrator_prompt = f"""You are the buildOS orchestrator for building sustainability analysis.

**User Request**: "{message}"
**IFC File**: {file_path if file_path else "No file provided"}
**Available Files**: {', '.join(available_files) if available_files else "None"}
**Session Context**: {session_context}/
**Session ID**: {session_id}
{continuation_note}

## ⚠️ CRITICAL WORKFLOW RULES

1. **PARALLEL BATCH PROCESSING** - Spawn ALL batch Tasks in a SINGLE message for parallel execution
2. **DELEGATE, don't do** - YOU do NOT classify elements, subagents do
3. **Wait for ALL Tasks** - After spawning parallel Tasks, wait for all results before aggregating
4. **Aggregate after ALL Tasks** - Use `mcp__ifc__aggregate_batch_results` only after all batches complete

## 🚫 FORBIDDEN ACTIONS FOR ORCHESTRATOR

You are the ORCHESTRATOR. You coordinate, you do NOT do the work yourself:
- ❌ Do NOT read batches.json to classify elements yourself
- ❌ Do NOT read CLASSIFICATION.md (that's for the batch-processor agent)
- ❌ Do NOT write batch_N_elements.json (that's the subagent's output)
- ❌ Do NOT classify elements yourself - ALWAYS delegate to batch-processor
- ✅ DO spawn ALL batch Tasks in PARALLEL (one message, multiple Task calls)
- ✅ DO wait for all Task results before proceeding
- ✅ DO use aggregate_batch_results AFTER all Tasks return

## Workflow Status Tool

Before starting, check workflow status:
```
Tool: mcp__ifc__get_workflow_status
Parameters: {{"session_context": "{session_context}"}}
```

This shows what stages are complete and recommends next steps.

## Skill-Based Workflow

For IFC analysis and CO2 calculations, read the skill file:
**Skill Guide**: $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/SKILL.md

## Correct Batch Processing Workflow

### Step 1: Parse
```
mcp__ifc__parse_ifc_file(ifc_path, output_path="{session_context}/parsed_data.json")
```

### Step 2: Prepare Batches
```
mcp__ifc__prepare_batches(json_path="{session_context}/parsed_data.json", batch_size=50, output_path="{session_context}/batches.json")
```

### Step 3: Classify (DELEGATE TO SUBAGENTS IN PARALLEL!)

⚠️ **YOU DO NOT CLASSIFY** - You spawn agents who do the classification.

🚀 **PARALLEL EXECUTION - SPAWN ALL BATCHES AT ONCE!** 🚀

Spawn ALL batch-processor Tasks in a SINGLE message for maximum parallelism.
This is REQUIRED for efficient processing and proper visualization.

**CORRECT (all tasks in one message - PARALLEL):**
```
Task: batch-processor (batch 1)
Task: batch-processor (batch 2)
Task: batch-processor (batch 3)
Task: batch-processor (batch 4)
→ All run in PARALLEL, results come back together
```

**WRONG (sequential - too slow):**
```
Message 1: Task: batch-processor (batch 1) → wait
Message 2: Task: batch-processor (batch 2) → wait
... this is INEFFICIENT!
```

**Spawn ALL batches like this (in ONE message):**
```
Task: batch-processor
  subagent_type: "batch-processor"
  description: "Classify batch 1"
  prompt: "Classify batch 1. Session: {session_context}/ Batch: 1"

Task: batch-processor
  subagent_type: "batch-processor"
  description: "Classify batch 2"
  prompt: "Classify batch 2. Session: {session_context}/ Batch: 2"

... (continue for all batches)
```

**What each subagent does (NOT you):**
- Reads batches.json
- Reads CLASSIFICATION.md
- Classifies its assigned batch
- Writes batch_N_elements.json
- Returns summary

**What YOU do:**
- Spawn ALL batch Tasks in ONE message (parallel)
- Wait for ALL results to come back
- Then proceed to aggregation

**DO NOT** read batches.json, CLASSIFICATION.md, or write batch files yourself!

### Step 4: Aggregate Results (AFTER Tasks Return!)
After ALL batch-processor Tasks have returned:
```
mcp__ifc__aggregate_batch_results(session_context="{session_context}", total_batches=N, output_file="{session_context}/all_classified_elements.json")
```

### Step 5: Calculate CO2
Use the aggregated file:
```
mcp__ifc__calculate_co2(classified_path="{session_context}/all_classified_elements.json", ...)
```

### Step 6: Generate Report
Use the CO2 report file:
```
mcp__ifc__generate_excel_report(data_json="{session_context}/co2_report.json", ...)
```

## Quick Reference

| Step | Tool/Script | Purpose |
|------|-------------|---------|
| Parse IFC | `mcp__ifc__parse_ifc_file` | Extract building elements |
| Prepare Batches | `mcp__ifc__prepare_batches` | Split for processing |
| Classify | Task agents (batch-processor) | Material classification |
| **Aggregate** | `mcp__ifc__aggregate_batch_results` | Combine batch results |
| Calculate CO2 | `mcp__ifc__calculate_co2` | CO2 impact calculation |
| Generate PDF | `mcp__ifc__generate_pdf_report` | Create PDF report (ReportLab) |
| Generate Excel | `mcp__ifc__generate_excel_report` | Create Excel spreadsheet |
| Generate PPTX | `mcp__ifc__generate_presentation` | Create PowerPoint |

## Session Context

All intermediate files go in: {session_context}/
- parsed_data.json
- batches.json
- batch_N_elements.json (per batch)
- all_classified_elements.json (aggregated)
- co2_report.json
- report.xlsx / report.pdf

## Important Paths

- Skill scripts: $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/scripts/
- Reference data: $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/reference/
- Database: $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/reference/durability_database.json

**REMEMBER: You are the ORCHESTRATOR, not the WORKER.**
- SPAWN ALL batch Tasks in PARALLEL (one message, multiple Task calls)
- WAIT for ALL Task results before proceeding to aggregation
- Read each Task's return message (e.g., "✅ Batch 1 complete")
- Never classify elements yourself
- Never write batch files yourself
- Use aggregate_batch_results AFTER all Tasks complete
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
