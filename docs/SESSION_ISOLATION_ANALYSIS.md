# Analysis: Session Isolation Issues & Proposed Solution

## 🔴 Problem Summary

### Issue 1: No File Upload Tracking
**Log Evidence:**
```json
{"event": "user_message", "file_path": null}
{"event": "system_context", "available_files": []}
```

**Problem:** User asked "how many beams in the model?" but no file was provided to the orchestrator.

### Issue 2: Orchestrator Accesses Old Data
**Log Evidence:**
```json
{"event": "model_thinking", "thinking": "I can see there are already parsed JSON files available..."}
{"event": "tool_call", "tool_name": "Bash", "tool_input": {"command": "ls -la"}}
{"event": "tool_call", "tool_name": "Read", "tool_input": {"file_path": "/Users/.../workspace/ifc_parsed.json"}}
```

**Problem:** Orchestrator used Bash commands to find `workspace/ifc_parsed.json` from a previous session, contaminating results.

### Issue 3: No Session Isolation
**Current Structure:**
```
workspace/
  ├── ifc_parsed.json          ← SHARED (from old session)
  ├── parsed_test.json         ← SHARED (from old session)
  └── .context/
      └── session_abc12345/    ← Session-specific (but SDK doesn't use it!)
```

**Problem:** SDK's `cwd` is set to `./workspace`, giving access to all old files.

### Issue 4: Orchestrator Can Escape
**Tool Access:**
```python
allowed_tools=[
    "Task",
    "Read",
    "Write", 
    "Bash",     ← Can explore anywhere!
    "mcp__ifc__*"
]
```

**Problem:** `Bash` tool allows orchestrator to search parent directories and find old data.

---

## ✅ Proposed Solution: Strict Session Isolation

### 1. **Session-Specific Workspace**

Each session should work in complete isolation:

```
workspace/
  └── sessions/
      ├── session_abc12345/          ← THIS session only
      │   ├── uploads/
      │   │   └── Small_condo.ifc
      │   ├── parsed/
      │   │   └── ifc_parsed.json
      │   └── output/
      │       ├── batches.json
      │       └── report.pdf
      └── session_def67890/          ← DIFFERENT session
          └── ...
```

**Benefits:**
- No cross-contamination
- Easy to debug (one folder per session)
- Can delete old sessions safely
- Clear data lineage

### 2. **Set SDK `cwd` to Session Folder**

```python
# BEFORE (Wrong - access to shared workspace)
options = ClaudeAgentOptions(
    cwd=str(workspace),  # ./workspace
)

# AFTER (Correct - isolated session)
session_workspace = workspace / "sessions" / session_id[:8]
session_workspace.mkdir(parents=True, exist_ok=True)

options = ClaudeAgentOptions(
    cwd=str(session_workspace),  # ./workspace/sessions/abc12345/
)
```

**Result:** Orchestrator can only see files in its own session folder.

### 3. **Copy Uploaded Files to Session Folder**

```python
if file_path:
    # Copy uploaded file to session workspace
    session_file = session_workspace / "uploads" / Path(file_path).name
    session_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, session_file)
    
    # Update prompt to use session-local path
    ifc_file_path = f"uploads/{Path(file_path).name}"
else:
    ifc_file_path = None
```

**Result:** Each session has its own copy, no shared state.

### 4. **Restrict Tool Access (Optional)**

For stricter isolation, remove `Bash` tool access:

```python
allowed_tools=[
    "Task",           # Spawn agents
    "Read",           # Read files (restricted to cwd)
    "Write",          # Write files (restricted to cwd)
    # "Bash",         # REMOVED - prevents exploration
    "mcp__ifc__*"     # IFC tools only
]
```

**Alternative:** Keep Bash but limit with `--workdir` or sandboxing.

### 5. **Improved Orchestrator Prompt**

```python
orchestrator_prompt = f"""You are the buildOS orchestrator.

**User Request**: "{message}"
**IFC File Available**: {"uploads/" + Path(file_path).name if file_path else "NO FILE - Ask user to upload one"}
**Session Workspace**: {session_workspace}/ (isolated, clean slate)
**Session ID**: {session_id}

IMPORTANT CONSTRAINTS:
- You are in an ISOLATED session workspace
- NO previous data exists - start fresh
- If no IFC file provided, ask user to upload one
- Use ONLY the IFC file in uploads/ folder
- Save all outputs to output/ folder

Your workflow:
1. Check if IFC file exists in uploads/ folder
2. If missing, return error: "Please upload an IFC file first"
3. If present, proceed with analysis:
   - Parse IFC → parsed/ifc_parsed.json
   - Create batches → output/batches.json
   - Classify → output/classified.json
   - Calculate → output/results.json
   - Generate report → output/report.pdf

Do NOT search for files outside your session workspace.
"""
```

---

## 🏗️ **Better Agent Flow**

### Current Flow (Problematic):
```
User Query → Orchestrator → Bash commands → Find old data → Wrong answer
```

### Proposed Flow (Clean):
```
User Query
    ↓
Check: File uploaded?
    ├─ NO → Return: "Please upload IFC file"
    ↓
    YES → Copy to session/uploads/
    ↓
Orchestrator (in session workspace)
    ↓
Check: uploads/file.ifc exists?
    ├─ NO → Error
    ↓
    YES → Parse IFC
    ↓
Create batches → output/batches.json
    ↓
Classify elements → output/classified.json
    ↓
Calculate CO2 → output/results.json
    ↓
Generate report → output/report.pdf
    ↓
Return: Results + file paths
```

---

## 📋 Implementation Checklist

### orchestrator.py Changes:
- [ ] Create session-specific workspace folder
- [ ] Copy uploaded file to session/uploads/
- [ ] Set SDK cwd to session workspace
- [ ] Update prompt with session-local paths
- [ ] Add file existence check before processing
- [ ] Log session workspace path

### apps/server/src/orchestrator.ts Changes:
- [ ] Validate file exists before calling Python
- [ ] Pass absolute path to uploaded file
- [ ] Return error if no file and query needs one

### Frontend Changes (Optional):
- [ ] Show "Please upload file" if query needs one
- [ ] Clear indication of which file is active
- [ ] Session workspace cleaner (delete old sessions)

---

## 🎯 Expected Behavior After Fix

### Scenario 1: Query with NO file uploaded
```
User: "How many beams?"
System: "Please upload an IFC file first to analyze the model."
```

### Scenario 2: Query with file uploaded
```
User uploads: Small_condo.ifc
User: "How many beams?"

Session workspace: workspace/sessions/abc12345/
  uploads/Small_condo.ifc      ← Copied here
  
Orchestrator:
  1. Checks uploads/Small_condo.ifc exists ✓
  2. Parses → parsed/ifc_parsed.json
  3. Queries beams
  4. Returns: "8 beams found"
  
NO access to old workspace/ifc_parsed.json ✓
```

### Scenario 3: Multiple concurrent sessions
```
Session A (abc12345): Small_condo.ifc
Session B (def67890): Large_building.ifc

Each works in isolation:
  workspace/sessions/abc12345/  ← Session A
  workspace/sessions/def67890/  ← Session B
  
NO cross-contamination ✓
```

---

## 💡 Key Insights

1. **Root Cause:** SDK's `cwd` was set to shared `./workspace`, allowing access to old data
2. **Secondary Cause:** No uploaded file, so orchestrator searched and found old data
3. **Solution:** Session-specific folders + proper file upload handling
4. **Benefit:** Complete session isolation, reproducible results, easy debugging

---

## 🚀 Next Steps

Would you like me to:
1. ✅ Implement session isolation in orchestrator.py
2. ✅ Update prompt to prevent exploration
3. ✅ Add file validation before processing
4. ✅ Create workspace cleanup script
5. ✅ Update documentation with new architecture

Let me know and I'll implement the fix!
