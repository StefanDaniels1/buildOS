# buildOS Observability - Quick Start Guide

## Overview

The buildOS IFC analysis orchestrator now has **full observability** through a real-time dashboard. Watch your IFC parsing, batch processing, and AI classification agents work in real-time.

## 🚀 How to Run

### Option 1: Automated Script (Recommended)

```bash
./run_buildos.sh Small_condo.ifc
```

This script will:
- ✅ Check if the dashboard is running (and start it if needed)
- ✅ Run the IFC analysis with event tracking
- ✅ Send events to the observability dashboard
- ✅ Show you the timeline URL when complete

### Option 2: Manual (Dashboard Already Running)

```bash
python run_with_dashboard.py Small_condo.ifc
```

## 📊 Dashboard

Once running, open your browser to:

**Dashboard**: http://localhost:5173
**Server API**: http://localhost:4000

## What You'll See

The dashboard shows a real-time timeline of all events:

### Event Types

| Event | Description | Example |
|-------|-------------|---------|
| **SessionStart** | Analysis begins | New IFC file loaded |
| **UserPromptSubmit** | What task is being executed | "Analyze Small_condo.ifc for CO2 impact" |
| **Stop** | Analysis completes | Status: success/error |
| **SessionEnd** | Session terminates | Cleanup complete |

### Session Info

Each analysis session has:
- **Session ID**: `buildos-HHMMSS` (timestamp-based)
- **Source App**: `buildOS`
- **Payload**: File name, prompts, status, error messages

## 🔍 How It Works

```
┌─────────────────────────────────────────┐
│  run_with_dashboard.py                  │
│  (Wrapper Script)                       │
└─────────────────┬───────────────────────┘
                  │
                  ├─► Send SessionStart event
                  │
                  ├─► Send UserPromptSubmit event
                  │
                  ├─► Run run.py (IFC analysis)
                  │   └─► Parse IFC
                  │   └─► Create batches
                  │   └─► Classify elements (AI)
                  │
                  ├─► Send Stop event (success/error)
                  │
                  └─► Send SessionEnd event
                       │
                       ▼
                  Dashboard Updates
                  (Real-time via WebSocket)
```

## 📁 Key Files

- **`run_buildos.sh`** - Main entry point (checks dashboard, runs analysis)
- **`run_with_dashboard.py`** - Wrapper that sends events to dashboard
- **`send_dashboard_event.py`** - Helper module for event transmission
- **`run.py`** - Core IFC orchestrator (unchanged)

## 🛠️ Architecture

### Event Sender (`send_dashboard_event.py`)

Simple HTTP POST to the observability server:

```python
send_event(
    "UserPromptSubmit",
    session_id="buildos-164829",
    payload={"prompt": "Analyze Small_condo.ifc"}
)
```

Sends to: `http://localhost:4000/events`

### Dashboard Server

- **Framework**: Bun.serve (Bun runtime)
- **Database**: SQLite (events stored locally)
- **Real-time**: WebSocket broadcasting
- **Location**: `claude-code-hooks-multi-agent-observability/`

### Dashboard Client

- **Framework**: Vue 3 + Vite
- **Features**: Timeline view, session filtering, event details
- **Location**: `claude-code-hooks-multi-agent-observability/apps/client/`

## 🔧 Starting the Dashboard Manually

If you need to start the dashboard separately:

```bash
cd claude-code-hooks-multi-agent-observability
export PATH="$HOME/.bun/bin:$PATH"
./scripts/start-system.sh
```

Wait ~3 seconds, then verify:

```bash
curl http://localhost:4000
# Should return: "Multi-Agent Observability Server"
```

## 🎯 Example Output

When running `./run_buildos.sh Small_condo.ifc`:

```
🏗️  buildOS with Dashboard Observability
==================================================
📊 Dashboard: http://localhost:5173
📁 IFC File: Small_condo.ifc
🔖 Session: buildos-164829
==================================================

🚀 Starting IFC analysis...
📊 Watch progress at: http://localhost:5173

[IFC analysis runs...]

✅ Analysis complete! Check the dashboard for full timeline.

📊 Review timeline: http://localhost:5173
🔖 Session ID: buildos-164829
```

## 🐛 Troubleshooting

### Dashboard not showing events?

1. Check server is running:
   ```bash
   curl http://localhost:4000/events/recent?limit=5
   ```

2. Check the session ID in your terminal output matches the dashboard

3. Refresh the dashboard browser tab

### Dashboard won't start?

1. Check if Bun is installed:
   ```bash
   bun --version
   ```

2. Install Bun if needed:
   ```bash
   curl -fsSL https://bun.sh/install | bash
   export PATH="$HOME/.bun/bin:$PATH"
   ```

3. Check if ports are already in use:
   ```bash
   lsof -i :4000
   lsof -i :5173
   ```

### Events not appearing?

Make sure you're using the wrapper script:

✅ **Correct**: `./run_buildos.sh Small_condo.ifc`
❌ **Wrong**: `python run.py Small_condo.ifc` (no events sent)

## 📚 Related Documentation

- **`RUN_WITH_CLAUDE.md`** - How to trigger hooks using Claude Code CLI
- **`OBSERVABILITY.md`** - Full observability documentation (if exists)
- **Original Dashboard**: https://github.com/anthropics/claude-code-hooks-multi-agent-observability

## 🎉 Success!

You now have full visibility into your buildOS IFC analysis pipeline. Watch as:

- ✅ IFC files are parsed (295 elements extracted)
- ✅ Classification batches are created (4 batches of 50 elements)
- ✅ AI agents classify concrete types in parallel
- ✅ Results are aggregated and validated

All in **real-time** on your dashboard!

---

**Questions?** Open the dashboard and watch your analysis in action at http://localhost:5173
