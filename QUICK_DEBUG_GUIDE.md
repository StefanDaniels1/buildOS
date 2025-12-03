# File Upload Debug - Quick Reference

## 🎯 What We Fixed

Added **comprehensive debug logging** at every step of the file upload chain to identify where data is lost.

## 🔍 Debug Points

```
┌─────────────────────────────────────────────────────────────┐
│  1. FILE UPLOAD (Sidebar)                                   │
│  ✅ App.vue: handleLeftUpload()                              │
│  📍 Console: "✅ App.vue: File added via left sidebar"       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. REACT TO PROP CHANGE                                     │
│  ✅ ChatWindow.vue: watch(props.availableFiles)              │
│  📍 Console: "🔍 ChatWindow: availableFiles prop changed"    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. SEND MESSAGE                                             │
│  ✅ ChatWindow.vue: sendMessage()                            │
│  📍 Console: "🔍 ChatWindow sending message with files"      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. BACKEND RECEIVES                                         │
│  ✅ index.ts: POST /api/chat                                 │
│  📍 Terminal: "📨 /api/chat received: available_files: 1"    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. SPAWN ORCHESTRATOR                                       │
│  ✅ orchestrator.ts: triggerOrchestrator()                   │
│  📍 Terminal: "[Orchestrator] Available files (1): [...]"    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. PYTHON RECEIVES                                          │
│  ✅ orchestrator.py: --available-files argument              │
│  📍 Session Log: "available_files": ["/path/to/file"]        │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Quick Test

1. **Upload file** → See "Loaded Files (1)" ✅
2. **Send message** → Check browser console 🔍
3. **Check backend** → See "📨 /api/chat received" 📡
4. **Run verification** → `./verify_fix.sh` ✓

## 📊 What Each Log Shows

| Location | Log Marker | Shows |
|----------|-----------|-------|
| Browser Console | ✅ App.vue: File added | File successfully stored in uploadedFiles array |
| Browser Console | 🔍 ChatWindow: availableFiles prop changed | React prop working correctly |
| Browser Console | 🔍 ChatWindow sending message | Actual data being sent to API |
| Backend Terminal | 📨 /api/chat received | Server received the data |
| Backend Terminal | [Orchestrator] Available files | Spawning Python with files |
| Session Log | "available_files": [...] | Python received and logged |

## ✅ Success Criteria

All these should be true:
- [x] File appears in "Loaded Files (1)" in UI
- [ ] Browser console shows uploadedFiles has 1 file
- [ ] Browser console shows sending availableFiles with 1 file
- [ ] Backend terminal shows received 1 file
- [ ] ./verify_fix.sh shows "✅ FIX IS WORKING!"

## 🚀 After It Works

Next steps:
1. Implement session-specific file tracking
2. Create isolated workspaces per session
3. Update orchestrator to use available files
4. Remove debug logs (or keep them?)

---

**Test it now and share the console output!**
