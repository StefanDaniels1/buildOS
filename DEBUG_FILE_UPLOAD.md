# Debug File Upload Issue

## Problem
Files uploaded via sidebar appear in UI ("Loaded Files (1)") but `available_files` is still empty in orchestrator logs.

## Changes Made

### Frontend (apps/client/src)

#### App.vue
- ✅ Added debug logging to `handleFileUploaded` (line 86-90)
- ✅ Added debug logging to `handleLeftUpload` (line 104-125)
- ✅ Passes `:available-files="uploadedFiles"` prop to ChatWindow (line 411)

#### ChatWindow.vue
- ✅ Added debug logging in `sendMessage` (line 65-70)
- ✅ Added watcher on `availableFiles` prop to track changes
- ✅ Sends `available_files` to backend (line 78)

### Backend (apps/server/src)

#### index.ts
- ✅ Added debug logging in `/api/chat` endpoint to log received data

#### orchestrator.ts
- ✅ Logs `availableFiles` when spawning Python orchestrator (line 28-30)
- ✅ Passes `--available-files` argument to Python script (line 79-85)

### Python (orchestrator.py)
- ✅ Parses `--available-files` argument (line 388)
- ✅ Logs to ConversationLogger (line 182-186)

## Testing Steps

### 1. Restart Services

```bash
# Terminal 1: Backend
cd apps/server
bun run src/index.ts

# Terminal 2: Frontend  
cd apps/client
bun run dev
```

### 2. Test in Browser

1. Open http://localhost:5173 in browser
2. Open Browser DevTools (F12) → Console tab
3. Upload file via **left sidebar** (drag & drop or click)
4. Verify file appears under "Loaded Files (1)"
5. Send a message (e.g., "how many beams?")
6. **Check browser console** for:
   ```
   ✅ App.vue: File added via left sidebar: {...}
   🔍 ChatWindow: availableFiles prop changed: [...]
   🔍 ChatWindow sending message with files: {...}
   ```

### 3. Check Backend Logs

In Terminal 1 (backend), look for:
```
📨 /api/chat received: { available_files_count: 1, available_files: [...] }
[Orchestrator] Available files (1): [...]
```

### 4. Check Session Logs

```bash
./verify_fix.sh
```

Expected output:
```
✅ FIX IS WORKING!
   available_files: 1 file(s)
   /Users/.../uploads/1234567890_Small_condo.ifc
```

## Potential Issues

### Issue 1: Frontend Not Rebuilt
**Symptom**: Changes not reflected in browser
**Fix**: 
```bash
cd apps/client
# Stop dev server (Ctrl+C)
bun run dev
# Hard refresh browser: Cmd+Shift+R
```

### Issue 2: uploadedFiles Array Not Reactive
**Symptom**: Files in UI but console shows empty array
**Check**: Browser console should show watcher firing:
```
🔍 ChatWindow: availableFiles prop changed: [{...}]
```
**If not firing**: The prop isn't being passed or is stale

### Issue 3: File Paths Not Absolute
**Symptom**: availableFiles has relative paths
**Check**: Backend log should show:
```
[Orchestrator] Resolved file: /absolute/path/to/file
```

### Issue 4: Session Isolation
**Note**: Current design passes ALL uploaded files to orchestrator.
For session isolation, we need to:
1. Track which files belong to which session
2. Only pass session-specific files
3. Create session-specific workspaces

## Quick Debug Commands

```bash
# Check latest session log
tail -20 .logs/conversations/*.jsonl | jq .

# Check if server is receiving files
cd apps/server && grep -r "available_files" src/

# Check frontend build
cd apps/client && ls -la dist/

# Check uploaded files
ls -lh uploads/
```

## Expected Flow

```
User uploads file via sidebar
    ↓
handleLeftUpload() → POST /api/upload
    ↓
File saved to uploads/
    ↓
uploadedFiles.push({name, path, absolutePath, timestamp})
    ↓
Browser console: "✅ App.vue: File added via left sidebar"
    ↓
ChatWindow receives :available-files prop (reactive)
    ↓
Browser console: "🔍 ChatWindow: availableFiles prop changed"
    ↓
User sends message
    ↓
sendMessage() → POST /api/chat with available_files array
    ↓
Backend console: "📨 /api/chat received: { available_files_count: 1 }"
    ↓
triggerOrchestrator() → python3 orchestrator.py --available-files [...]
    ↓
Python logs system_context with available_files
    ↓
Session log shows: "available_files": ["/absolute/path"]
    ↓
✅ SUCCESS
```

## Next Steps After Fix

1. **Verify with ./verify_fix.sh**
2. **Test multiple file uploads**
3. **Implement session isolation** (files per session, not global)
4. **Update orchestrator prompt** to use available_files
5. **Test file parsing** with orchestrator
