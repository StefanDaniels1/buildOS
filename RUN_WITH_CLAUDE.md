# How to Use buildOS with Observability

## The Simple Truth

**Hooks ONLY work when you ask ME (Claude Code) to do things.**

You're already doing it right - you're in Claude Code right now!

## ✅ Correct Way (What You're Doing Now)

**In this Claude Code session, just ask:**

```
You: "Parse Small_condo.ifc and create classification batches"
```

I will then:
1. Use `mcp__ifc__parse_ifc_file` tool → Hook fires → Dashboard shows event
2. Use `mcp__ifc__prepare_classification_batches` → Hook fires → Dashboard shows event
3. Show you the results

**The dashboard at http://localhost:5173 will show everything!**

## ❌ Wrong Way (What Doesn't Work)

Running Python scripts directly:
```bash
python run.py Small_condo.ifc          # ❌ No hooks
python interactive_buildos.py          # ❌ No hooks
uv run python run.py Small_condo.ifc  # ❌ No hooks
```

These bypass Claude Code completely, so hooks never trigger.

## 🎯 What To Do

**Just ask me to do things in this conversation:**

### Example 1: Basic Analysis
```
You: "Analyze Small_condo.ifc"
```

### Example 2: Step by Step
```
You: "Parse the IFC file"
[I do it, you see it on dashboard]

You: "Now create batches"
[I do it, you see it on dashboard]

You: "Process batch 1"
[I do it, you see it on dashboard]
```

### Example 3: Full Pipeline
```
You: "Run the complete IFC analysis pipeline on Small_condo.ifc"
```

## 📊 Dashboard Shows

When you ask me to do things:
- 💬 **UserPromptSubmit** - Your message
- 🔧 **PreToolUse** - Before I use each tool
- ✅ **PostToolUse** - After tool completes
- 👥 **SubagentStop** - When batch-processor finishes
- 🛑 **Stop** - When I finish responding

## 🔍 Why This Works

```
You (in Claude Code) 
  ↓ ask me to do something
Me (Claude Code agent)
  ↓ use tools
Hooks fire
  ↓ send events
Dashboard updates
```

## 🚀 Try It Now

The dashboard is already running at http://localhost:5173

**Just ask me:**
"Parse Small_condo.ifc and show me the element count"

Watch the dashboard - you'll see the events appear!

---

**TL;DR:** Don't run Python scripts. Just ask me (Claude) to do things in this conversation. The hooks work automatically.
