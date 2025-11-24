# Using buildOS Observability Dashboard

## ✅ System Status

- **Dashboard**: http://localhost:5173 (running)
- **Server**: http://localhost:4000 (running)  
- **Hooks**: Installed in `.claude/` (configured)

## 🎯 How to Use

The observability system captures events when you use **Claude Code CLI** (not when running Python scripts directly).

### Method 1: Use Claude Code CLI (Recommended)

**In this Claude Code session, ask Claude to:**

```
Run the IFC analysis on Small_condo.ifc using the buildOS system
```

Claude will then use the tools (`mcp__ifc__parse_ifc_file`, `mcp__ifc__prepare_classification_batches`, `Task`) and the hooks will capture all activity.

### Method 2: Test Hooks Manually

Send a test event to verify the connection:

```bash
echo '{"session_id": "test-manual", "tool_use": {"name": "TestTool", "input": {}}, "transcript_path": ""}' | \
  uv run .claude/hooks/send_event.py --source-app buildOS --event-type PreToolUse
```

Then check http://localhost:5173 - you should see the test event appear!

## 🔍 What Gets Captured

When you use Claude Code to run buildOS operations:

1. **UserPromptSubmit** - Your request to Claude
2. **PreToolUse** - Before each tool runs:
   - `mcp__ifc__parse_ifc_file` 
   - `mcp__ifc__prepare_classification_batches`
   - `Task` (spawning batch-processor agent)
3. **PostToolUse** - After each tool completes
4. **SubagentStop** - When batch-processor agent finishes
5. **Stop** - When Claude's response is complete
6. **SessionStart/SessionEnd** - Session lifecycle

## 🎨 Dashboard Features

- **Real-time updates** via WebSocket
- **Color-coded events** by type
- **Session tracking** (buildOS:abc12345)
- **Tool names** and inputs/outputs
- **Live pulse chart** showing activity
- **Filtering** by app, session, event type
- **Chat transcripts** (click on Stop events)

## 🧪 Example Usage

### In Claude Code CLI:

**You:** "Parse Small_condo.ifc and create batches for classification"

**Claude will:**
1. Call `mcp__ifc__parse_ifc_file` → Hook captures PreToolUse
2. Tool completes → Hook captures PostToolUse  
3. Call `mcp__ifc__prepare_classification_batches` → Hooks capture it
4. Report results → Hook captures Stop event

**Dashboard shows:** Full timeline of operations with timestamps, tool names, and success/failure indicators.

### With Agents:

**You:** "Process batch 1 using the batch-processor agent"

**Claude will:**
1. Spawn Task tool with batch-processor agent → PreToolUse captured
2. Batch-processor runs (in separate session) → Its events captured with different session_id
3. Batch-processor completes → SubagentStop captured
4. Main session continues → PostToolUse captured

**Dashboard shows:** Two parallel sessions (orchestrator and batch-processor) with different colors!

## 🔧 Why Direct Python Scripts Don't Trigger Hooks

When you run `uv run python run.py Small_condo.ifc`, you're executing Python directly, bypassing Claude Code. The hooks are part of Claude Code's lifecycle and only trigger when Claude Code itself executes tools.

**Solution:** Use Claude Code to orchestrate the workflow, which will then trigger hooks at every step.

## 📊 Current Test Event

The dashboard currently shows 1 test event we sent earlier. Once you ask Claude to run the IFC analysis, you'll see the real buildOS workflow appear!

## 🛑 Stopping the Dashboard

```bash
cd /Users/stefandaniels/Documents/BIMAI/BIMAI_V3/agent_system4/claude-code-hooks-multi-agent-observability
./scripts/reset-system.sh
```

Or just close the terminal where the dashboard is running.

---

**Ready to see it in action?** Ask Claude Code to process an IFC file and watch the dashboard light up! 🚀
