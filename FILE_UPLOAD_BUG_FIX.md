# File Upload Bug - Root Cause & Fix

## 🔴 **ROOT CAUSE IDENTIFIED**

### The Problem

When a user uploads a file in ChatWindow and then sends a message:
- `file_path`: `null` ❌
- `available_files`: `[]` ❌

### Why It Happens

There are **TWO different upload paths** that behave differently:

#### Path 1: Left Sidebar Upload
```typescript
// App.vue - handleLeftUpload()
async function handleLeftUpload(file: File) {
  const res = await fetch(`${API_BASE_URL}/api/upload`, ...);
  const data = await res.json();
  if (data.success) {
    uploadedFilePath.value = data.file.path;
    uploadedFiles.value.push({              ← ✅ ADDS to array
      name: data.file.name,
      path: data.file.path,
      absolutePath: data.file.absolutePath,
      timestamp: Date.now()
    });
  }
}
```

#### Path 2: ChatWindow Upload (**BROKEN**)
```typescript
// ChatWindow.vue - handleFileUpload()
async function handleFileUpload(file: File) {
  const res = await fetch(`${API_BASE_URL}/api/upload`, ...);
  const data = await res.json();
  if (data.success) {
    uploadedFile.value = { ... };           ← Stores locally
    emit('fileUploaded', data.file.path);   ← ❌ Only emits path string!
  }
}

// App.vue - handleFileUploaded()
function handleFileUploaded(filePath: string) {
  uploadedFilePath.value = filePath;        ← Sets path
  // ❌ Does NOT add to uploadedFiles array!
}
```

### The Result

```
User uploads in ChatWindow
  → emit('fileUploaded', '/path/to/file')
  → App.vue receives: filePath string only
  → uploadedFilePath.value = '/path/to/file' ✅
  → uploadedFiles array = [] ❌ (NOT updated!)
  
User sends message
  → available_files: props.availableFiles.map(...)
  → availableFiles = [] (empty!)
  → Orchestrator receives: available_files: []
  → ❌ NO FILES AVAILABLE!
```

---

## ✅ **THE FIX**

### Option 1: Emit Full File Object (Recommended)

**ChatWindow.vue:**
```typescript
async function handleFileUpload(file: File) {
  const res = await fetch(`${API_BASE_URL}/api/upload`, ...);
  const data = await res.json();
  if (data.success) {
    uploadedFile.value = {
      name: data.file.name,
      path: data.file.path,
      absolutePath: data.file.absolutePath
    };
    // ✅ Emit full file object instead of just path
    emit('fileUploaded', {
      name: data.file.name,
      path: data.file.path,
      absolutePath: data.file.absolutePath,
      timestamp: Date.now()
    });
  }
}
```

**App.vue:**
```typescript
function handleFileUploaded(file: {name: string, path: string, absolutePath: string, timestamp: number}) {
  uploadedFilePath.value = file.path;
  // ✅ Add to uploadedFiles array
  uploadedFiles.value.push(file);
}
```

**Update emit type in ChatWindow.vue:**
```typescript
const emit = defineEmits<{
  (e: 'sessionCreated', sessionId: string): void;
  (e: 'fileUploaded', file: {name: string, path: string, absolutePath: string, timestamp: number}): void;
  (e: 'initialConsumed'): void;
}>();
```

---

## 🎯 **EXPECTED BEHAVIOR AFTER FIX**

### Before Fix:
```
User uploads file in ChatWindow
  → uploadedFilePath = '/uploads/file.ifc' ✅
  → uploadedFiles = [] ❌
  → Message sent with available_files: [] ❌
  → Orchestrator has NO access to file ❌
```

### After Fix:
```
User uploads file in ChatWindow
  → uploadedFilePath = '/uploads/file.ifc' ✅
  → uploadedFiles = [{name, path, absolutePath, timestamp}] ✅
  → Message sent with available_files: [absolutePath] ✅
  → Orchestrator receives file! ✅
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

- [ ] Update ChatWindow.vue emit to send full file object
- [ ] Update App.vue handleFileUploaded to accept file object
- [ ] Update App.vue handleFileUploaded to add file to array
- [ ] Test file upload in ChatWindow
- [ ] Verify uploadedFiles array is populated
- [ ] Verify available_files is sent to orchestrator
- [ ] Test with session logs

---

## 🧪 **TESTING**

### Test Scenario:
1. Open dashboard
2. Upload file in ChatWindow (drag/drop or select)
3. Send message: "how many beams?"
4. Check logs: `python analyze_logs.py --analyze 0`
5. Verify:
   - `file_path`: not null ✅
   - `available_files`: has file path ✅
   - Orchestrator can access file ✅

---

## 💡 **BONUS: Session Isolation Fix**

Once files are passed correctly, we still need session isolation.

Currently:
```
orchestrator.py:
  cwd=str(workspace)  ← ./workspace (shared!)
```

Should be:
```
orchestrator.py:
  session_workspace = workspace / "sessions" / session_id[:8]
  cwd=str(session_workspace)  ← ./workspace/sessions/abc12345/
```

But let's fix the file passing first, then tackle session isolation!
