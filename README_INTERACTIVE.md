# buildOS Interactive Mode

Interactive conversation-based orchestrator for IFC CO2 analysis with full observability.

## 🚀 Quick Start

### 1. Start the Observability Dashboard (Optional but Recommended)

```bash
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh
```

Open http://localhost:5173 to watch agent activity in real-time.

### 2. Launch buildOS Interactive Session

```bash
python interactive_buildos.py
```

### 3. Have a Conversation!

```
[Turn 1] 💬 You: Analyze Small_condo.ifc for CO2 impact

[Turn 1] 🤖 Claude:
I'll analyze the IFC file for CO2 impact assessment...
🔧 Using tool: mcp__ifc__parse_ifc_file
✓ Parsing complete. Found 155 geometric elements.
🔧 Using tool: mcp__ifc__prepare_classification_batches
✓ Created 4 batches for parallel processing.
...

[Turn 2] 💬 You: Process batch 1 with the batch-processor agent

[Turn 2] 🤖 Claude:
I'll process batch 1 using the batch-processor agent...
🔧 Using tool: Task
✓ Batch processing complete! 50 elements classified.
...
```

## 🎯 Why Interactive Mode?

### The Problem with Direct Scripts

When you run `uv run python run.py Small_condo.ifc`:
- ❌ Hooks don't fire (not using Claude Code lifecycle)
- ❌ No dashboard events
- ❌ No observability
- ❌ One-shot execution (no context memory)

### The Solution: Interactive Session

When you use `python interactive_buildos.py`:
- ✅ Hooks fire on every tool use
- ✅ Dashboard shows real-time activity
- ✅ Full observability of agent workflow
- ✅ Context memory across turns
- ✅ Natural conversation flow

## 💡 Example Conversations

### Basic Analysis

```
You: Parse Small_condo.ifc
Claude: [parses IFC, extracts 295 elements]

You: How many geometric elements?
Claude: Found 155 geometric elements (remembers from previous turn!)

You: Create batches of 50 elements each
Claude: [creates 4 batches]

You: Process batch 1
Claude: [spawns batch-processor agent, classifies 50 elements]
```

### Multi-Step Workflow

```
You: Analyze the IFC file and process all batches

Claude: I'll execute the full workflow:
1. Parsing IFC... ✓ (155 geometric elements)
2. Creating batches... ✓ (4 batches)
3. Processing batch 1... ✓ (50 elements)
4. Processing batch 2... ✓ (50 elements)
5. Processing batch 3... ✓ (50 elements)
6. Processing batch 4... ✓ (5 elements)
All done! 155 elements classified.
```

### Debugging & Exploration

```
You: What's in the first batch?
Claude: [reads .context/.../batches.json, shows batch 1 details]

You: Show me element types in batch 1
Claude: [analyzes batch 1, lists: 8 beams, 17 ceilings, 8 footings, 17 doors]

You: Why did classification fail for element abc123?
Claude: [reads batch output, explains missing material data]
```

## 🎨 Commands

| Command | Action |
|---------|--------|
| `exit` | End session and quit |
| `interrupt` | Stop current task (if running) |
| `new` | Start fresh session (clear context) |
| `status` | Show workspace status |

## 📊 Dashboard Integration

When you use interactive mode, the dashboard at http://localhost:5173 shows:

1. **UserPromptSubmit** - Your message to Claude
2. **PreToolUse** - Before each tool execution
3. **PostToolUse** - After tool completes
4. **SubagentStop** - When batch-processor finishes
5. **Stop** - When Claude completes response

**Two Sessions Visible:**
- Main orchestrator (your session)
- Batch-processor agent (spawned session)

Different session colors help distinguish parallel work!

## 🔍 What Makes This Work?

### Context Memory

```python
# Turn 1
You: "Parse model.ifc"
Claude: [parses, stores info in context]

# Turn 2
You: "How many elements?"
Claude: "The file has 155 elements"  # Remembers!

# Turn 3
You: "Create batches"
Claude: [uses parsed data from Turn 1]  # Context works!
```

### Hook Firing

Every tool use triggers hooks:
```
You send prompt → UserPromptSubmit hook fires
Claude uses tool → PreToolUse hook fires
Tool executes → PostToolUse hook fires
Claude responds → Stop hook fires
```

All events → Server → Dashboard (real-time updates!)

## 🧪 Testing Observability

### 1. Start Dashboard
```bash
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh
```

### 2. Start buildOS
```bash
python interactive_buildos.py
```

### 3. Send Simple Command
```
You: Parse Small_condo.ifc
```

### 4. Watch Dashboard
You should see:
- 💬 UserPromptSubmit: "Parse Small_condo.ifc"
- 🔧 PreToolUse: mcp__ifc__parse_ifc_file
- ✅ PostToolUse: mcp__ifc__parse_ifc_file ✓
- 🛑 Stop

If you see these events, observability is working! 🎉

## 🚦 Status Line

The status line at the bottom of the terminal shows:
```
[buildOS] | [Claude 3.5 Sonnet] | [abc12345] | 🔧 parse_ifc_file
```

Real-time indicator of what the agent is doing!

## 📝 Comparison

| Feature | `run.py` (old) | `interactive_buildos.py` (new) |
|---------|----------------|-------------------------------|
| Execution | One-shot | Interactive conversation |
| Context memory | ❌ | ✅ |
| Hooks fire | ❌ | ✅ |
| Dashboard events | ❌ | ✅ |
| Multi-turn | ❌ | ✅ |
| Debugging | Hard | Easy (ask questions!) |
| Flexibility | Fixed workflow | Dynamic |

## 🎯 Use Cases

### Development
```
You: Parse the IFC and tell me about the structure
Claude: [analyzes, explains building hierarchy]

You: What element types are most common?
Claude: [counts, reports: 17 ceilings, 8 beams, etc.]

You: Process just the structural elements
Claude: [filters, processes subset]
```

### Debugging
```
You: Why did batch 1 take so long?
Claude: [checks logs, explains: 50 elements, complex materials]

You: Show me the last error
Claude: [reads output, displays error details]
```

### Experimentation
```
You: Try batch size of 25 instead of 50
Claude: [recreates batches with new size]

You: Compare results
Claude: [analyzes both outputs, shows differences]
```

## 🔧 Advanced: Custom Workflows

You can have Claude execute custom workflows:

```
You: Run the full pipeline but skip batch 3

Claude: I'll process batches 1, 2, and 4 only:
- Batch 1: 50 elements... ✓
- Batch 2: 50 elements... ✓
- Batch 3: Skipped (as requested)
- Batch 4: 5 elements... ✓
Total: 105 elements classified.
```

## 📚 Best Practices

1. **Start with Dashboard** - Visual feedback is helpful
2. **Use 'status' command** - Check workspace before operations
3. **Ask questions** - Claude remembers context, ask for clarification
4. **Use 'interrupt'** - Stop long-running tasks if needed
5. **Use 'new'** - Fresh session for new IFC files

## 🐛 Troubleshooting

### Hooks Not Firing

**Check:** Is Claude Code using the hooks?
```bash
cat .claude/settings.local.json
# Should show hook configurations
```

**Solution:** Hooks fire when Claude Code executes tools, which happens in interactive mode.

### Dashboard Not Updating

**Check:** Is the server running?
```bash
curl http://localhost:4000/events/recent
```

**Solution:** Start the dashboard:
```bash
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh
```

### No Context Memory

**Check:** Did you start a new session?
```
You: new  # This clears context!
```

**Solution:** Don't use 'new' unless you want to clear context.

---

**Ready to go?** Launch `python interactive_buildos.py` and start analyzing! 🚀
