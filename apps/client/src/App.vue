<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useWebSocket } from './composables/useWebSocket';
import { useTheme } from './composables/useTheme';
import AgentFlowTree from './components/AgentFlowTree.vue';
import ChatWindow from './components/ChatWindow.vue';
import EventTimeline from './components/EventTimeline.vue';
import SessionFilter from './components/SessionFilter.vue';
import IfcViewer from './components/IfcViewer.vue';
import MarkdownRenderer from './components/MarkdownRenderer.vue';
import ToolsBuilder from './components/ToolsBuilder.vue';
import { API_BASE_URL } from './config';
import BimaiLogo from './BIMAI.svg';

const { events, isConnected, error } = useWebSocket();
const { theme, toggleTheme } = useTheme();

// Welcome message state
const hasShownWelcome = ref(false);
const welcomeSessionId = ref('');

// Generate welcome messages that look like orchestrator events
// Only show on first visit ever (tracked in localStorage)
function showWelcomeMessages() {
  if (hasShownWelcome.value) return;

  // Check if user has seen welcome before
  const hasSeenWelcome = localStorage.getItem('buildos_welcome_shown');
  if (hasSeenWelcome) {
    hasShownWelcome.value = true;
    return;
  }

  const sessionId = `welcome_${Date.now()}`;
  welcomeSessionId.value = sessionId;
  const baseTime = Date.now();

  // Select the welcome session immediately so messages are visible
  selectedSession.value = sessionId;

  // Message 1: Thinking - Initializing
  setTimeout(() => {
    events.value.push({
      source_app: 'buildos-orchestrator',
      session_id: sessionId,
      hook_event_type: 'AgentThinking',
      payload: {
        thought: 'Initializing BIM AI orchestrator...',
        timestamp: new Date().toISOString()
      },
      timestamp: baseTime
    });
  }, 300);

  // Message 2: Thinking - Ready
  setTimeout(() => {
    events.value.push({
      source_app: 'buildos-orchestrator',
      session_id: sessionId,
      hook_event_type: 'AgentThinking',
      payload: {
        thought: 'System ready. Loading capabilities...',
        timestamp: new Date().toISOString()
      },
      timestamp: baseTime + 500
    });
  }, 800);

  // Message 3: Thinking - Hello preview
  setTimeout(() => {
    events.value.push({
      source_app: 'buildos-orchestrator',
      session_id: sessionId,
      hook_event_type: 'AgentThinking',
      payload: {
        thought: "Hello! I'm your BIM AI assistant...",
        timestamp: new Date().toISOString()
      },
      timestamp: baseTime + 1000
    });
  }, 1300);

  // Message 4: Complete - Full welcome message
  setTimeout(() => {
    events.value.push({
      source_app: 'buildos-orchestrator',
      session_id: sessionId,
      hook_event_type: 'Stop',
      payload: {
        status: 'success',
        message: `Hello! I'm your BIM AI assistant.

I can help you analyze IFC (Industry Foundation Classes) building models and extract valuable insights from your BIM data.

**What I can do:**
- Parse and analyze IFC files
- Extract building elements, materials, and quantities
- Perform various analyses on your building data
- Generate comprehensive reports (PDF, Excel)

**To get started:**
1. Upload an IFC file using the upload button below
2. Tell me what you'd like to analyze

**Example commands:**
- "Analyze the uploaded building"
- "List all building elements"
- "Generate a report"

Upload an IFC file and let me know how I can help!`,
        timestamp: new Date().toISOString()
      },
      timestamp: baseTime + 1500
    });

    hasShownWelcome.value = true;
    // Mark that user has seen welcome (persistent)
    localStorage.setItem('buildos_welcome_shown', 'true');
  }, 1800);
}

const selectedSession = ref<string | null>(null);
const showTimeline = ref(true);
const leftCollapsed = ref(false);
const rightCollapsed = ref(false);
const isLeftDragging = ref(false);
const leftFileInput = ref<HTMLInputElement | null>(null);
const isNewSession = ref(false); // Flag to track new session creation

// View mode: 'chat', 'viewer', or 'tools'
type ViewMode = 'chat' | 'viewer' | 'tools';
const viewMode = ref<ViewMode>('chat');

// Track uploaded file for viewer
const uploadedFilePath = ref<string | null>(null);
const viewerRef = ref<InstanceType<typeof IfcViewer> | null>(null);
const chatMessagesRef = ref<HTMLElement | null>(null);

// Track all uploaded files (history)
const uploadedFiles = ref<Array<{ name: string; path: string; absolutePath: string; timestamp: number }>>([]);

// API Key management & User Identity
const apiKey = ref('');
const userId = ref('');
const showApiKeyModal = ref(true); // Start with modal shown
const apiKeyInput = ref('');
const apiKeyError = ref('');
const isValidatingKey = ref(false);
const isAuthenticated = ref(false); // Only true when valid key is set

// Generate a user ID from API key using SHA-256 hash (first 16 chars)
async function generateUserId(key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex.substring(0, 16); // First 16 chars = 64 bits of entropy
}

// Load API key and user ID from localStorage on mount
onMounted(async () => {
  const savedKey = localStorage.getItem('anthropic_api_key');
  const savedUserId = localStorage.getItem('buildos_user_id');

  if (savedKey && savedUserId && savedKey.startsWith('sk-ant-')) {
    apiKey.value = savedKey;
    userId.value = savedUserId;
    isAuthenticated.value = true;
    showApiKeyModal.value = false;
    // Show welcome messages after connection established
    setTimeout(() => showWelcomeMessages(), 800);
  } else if (savedKey && savedKey.startsWith('sk-ant-')) {
    // Migrate: generate user ID for existing key
    apiKey.value = savedKey;
    userId.value = await generateUserId(savedKey);
    localStorage.setItem('buildos_user_id', userId.value);
    isAuthenticated.value = true;
    showApiKeyModal.value = false;
    setTimeout(() => showWelcomeMessages(), 800);
  } else {
    // No valid API key - force the modal to show
    showApiKeyModal.value = true;
    isAuthenticated.value = false;
  }
});

async function saveApiKey() {
  const key = apiKeyInput.value.trim();
  apiKeyError.value = '';

  if (!key) {
    apiKeyError.value = 'Please enter your API key';
    return;
  }

  // Validate key format
  if (!key.startsWith('sk-ant-')) {
    apiKeyError.value = 'Invalid format. Anthropic API keys start with "sk-ant-"';
    return;
  }

  if (key.length < 20) {
    apiKeyError.value = 'API key appears too short. Please check and try again.';
    return;
  }

  isValidatingKey.value = true;

  try {
    apiKey.value = key;
    userId.value = await generateUserId(key);
    localStorage.setItem('anthropic_api_key', apiKey.value);
    localStorage.setItem('buildos_user_id', userId.value);
    isAuthenticated.value = true;
    showApiKeyModal.value = false;
    apiKeyInput.value = '';
    // Show welcome messages for new login
    setTimeout(() => showWelcomeMessages(), 500);
  } catch (err) {
    apiKeyError.value = 'Error saving API key. Please try again.';
  } finally {
    isValidatingKey.value = false;
  }
}

function clearApiKey() {
  apiKey.value = '';
  userId.value = '';
  localStorage.removeItem('anthropic_api_key');
  localStorage.removeItem('buildos_user_id');
  isAuthenticated.value = false;
  showApiKeyModal.value = true; // Force modal to show again
}

function openApiKeySettings() {
  apiKeyInput.value = ''; // Don't pre-fill for security
  apiKeyError.value = '';
  showApiKeyModal.value = true;
}

// Stats
const stats = computed(() => {
  const sessions = new Set(events.value.map(e => e.session_id));
  const eventTypes = new Set(events.value.map(e => e.hook_event_type));
  return {
    totalEvents: events.value.length,
    sessions: sessions.size,
    eventTypes: eventTypes.size
  };
});

// Filter events by selected session
const displayedEvents = computed(() => {
  // If creating a new session, show empty state
  if (isNewSession.value) {
    return [];
  }
  
  if (selectedSession.value) {
    return events.value.filter(e => e.session_id === selectedSession.value);
  }
  // If no session selected, show the most recent session
  const uniqueSessions = new Map<string, typeof events.value[0]>();
  for (const event of events.value) {
    if (!uniqueSessions.has(event.session_id) || (event.timestamp || 0) > (uniqueSessions.get(event.session_id)?.timestamp || 0)) {
      uniqueSessions.set(event.session_id, event);
    }
  }
  const mostRecentSession = Array.from(uniqueSessions.values()).sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))[0]?.session_id;
  if (mostRecentSession) {
    return events.value.filter(e => e.session_id === mostRecentSession);
  }
  return [];
});

// Get current session events for viewer mode display
const sessionEvents = computed(() => {
  return displayedEvents.value;
});

// Chat component key to force reset on new session
const chatKey = computed(() => {
  return isNewSession.value ? 'new-session' : (selectedSession.value || 'default');
});

function handleSessionCreated(sessionId: string) {
  selectedSession.value = sessionId;
  isNewSession.value = false; // Clear new session flag once session is created
}

function handleSessionSelect(sessionId: string | null) {
  selectedSession.value = sessionId;
  isNewSession.value = false; // Clear new session flag when switching sessions
}

function handleFileUploaded(file: {name: string, path: string, absolutePath: string, timestamp: number}) {
  uploadedFilePath.value = file.path;
  // Add to uploaded files array so it's available to orchestrator
  uploadedFiles.value.push(file);
  console.log('✅ App.vue: File added via ChatWindow:', file, 'Total files:', uploadedFiles.value.length);
}

// Handle clicks on agent flow tree nodes - scroll to event in timeline
function handleFlowNodeClick(eventId: string) {
  // Find the event element in the DOM and scroll to it
  const eventElement = document.querySelector(`[data-event-id="${eventId}"]`);
  if (eventElement) {
    eventElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Add a highlight effect
    eventElement.classList.add('ring-2', 'ring-buildos-primary', 'ring-opacity-50');
    setTimeout(() => {
      eventElement.classList.remove('ring-2', 'ring-buildos-primary', 'ring-opacity-50');
    }, 2000);
  }
}

// Extract downloadable file paths from message content
function extractDownloadableFiles(message: string): Array<{ path: string; type: string; label: string }> {
  const files: Array<{ path: string; type: string; label: string }> = [];
  const seenPaths = new Set<string>();
  
  // Helper to add file if not seen
  const addFile = (rawPath: string, type: string, label: string) => {
    // Clean up the path - remove quotes, backticks, and surrounding whitespace
    const cleanPath = rawPath.replace(/^[\s"'`]+|[\s"'`]+$/g, '').trim();
    
    // Skip if empty or doesn't look like a path
    if (!cleanPath || cleanPath.length < 5) return;
    
    // Normalize the path for comparison (case-insensitive, handle Docker paths)
    let normalizedPath = cleanPath.toLowerCase();
    
    // Remove /app/ prefix for comparison (Docker container path)
    if (normalizedPath.startsWith('/app/')) {
      normalizedPath = normalizedPath.slice(4);
    }
    
    if (!seenPaths.has(normalizedPath)) {
      seenPaths.add(normalizedPath);
      files.push({ path: cleanPath, type, label });
      console.log(`📥 Found downloadable file: ${cleanPath} (${type})`);
    }
  };
  
  // Use simpler, more permissive regex patterns that work with various formats
  // These patterns match file paths ending with specific extensions
  
  // PDF files - match paths ending in .pdf
  const pdfRegex = /([^\s"'`()\[\]<>]+\.pdf)\b/gi;
  let match;
  while ((match = pdfRegex.exec(message)) !== null) {
    addFile(match[1], 'pdf', 'PDF Report');
  }
  
  // Excel files (.xlsx or .xls) - match paths ending in .xlsx or .xls
  const excelRegex = /([^\s"'`()\[\]<>]+\.xlsx?)\b/gi;
  while ((match = excelRegex.exec(message)) !== null) {
    addFile(match[1], 'excel', 'Excel Spreadsheet');
  }
  
  // PowerPoint files (.pptx or .ppt)
  const pptxRegex = /([^\s"'`()\[\]<>]+\.pptx?)\b/gi;
  while ((match = pptxRegex.exec(message)) !== null) {
    addFile(match[1], 'pptx', 'PowerPoint Presentation');
  }
  
  // Word documents (.docx or .doc)
  const docxRegex = /([^\s"'`()\[\]<>]+\.docx?)\b/gi;
  while ((match = docxRegex.exec(message)) !== null) {
    addFile(match[1], 'docx', 'Word Document');
  }
  
  return files;
}

// Legacy: Extract PDF path from message content (for backwards compatibility)
function extractPdfPath(message: string): string | null {
  const files = extractDownloadableFiles(message);
  const pdf = files.find(f => f.type === 'pdf');
  return pdf?.path || null;
}

// Get download URL for a file
function getDownloadUrl(filePath: string): string {
  // If it's already a full URL, return as-is
  if (filePath.startsWith('http')) {
    return filePath;
  }
  
  // Handle Docker container paths like /app/workspace/...
  if (filePath.includes('/app/workspace/')) {
    const relativePath = filePath.split('/app/workspace/')[1];
    return `${API_BASE_URL}/workspace/${relativePath}`;
  }
  
  // Handle workspace paths like /workspace/... or ./workspace/...
  if (filePath.includes('/workspace/')) {
    const relativePath = filePath.split('/workspace/')[1];
    return `${API_BASE_URL}/workspace/${relativePath}`;
  }
  
  // Handle paths that start with workspace/ (without leading slash)
  if (filePath.startsWith('workspace/')) {
    const relativePath = filePath.slice('workspace/'.length);
    return `${API_BASE_URL}/workspace/${relativePath}`;
  }
  
  // Handle paths that start with ./workspace/
  if (filePath.startsWith('./workspace/')) {
    const relativePath = filePath.slice('./workspace/'.length);
    return `${API_BASE_URL}/workspace/${relativePath}`;
  }
  
  // Handle Docker container uploads paths like /app/uploads/...
  if (filePath.includes('/app/uploads/')) {
    const relativePath = filePath.split('/app/uploads/')[1];
    return `${API_BASE_URL}/uploads/${relativePath}`;
  }
  
  // Handle uploads paths
  if (filePath.includes('/uploads/')) {
    const relativePath = filePath.split('/uploads/')[1];
    return `${API_BASE_URL}/uploads/${relativePath}`;
  }
  
  // Handle paths that start with uploads/ (without leading slash)
  if (filePath.startsWith('uploads/')) {
    const relativePath = filePath.slice('uploads/'.length);
    return `${API_BASE_URL}/uploads/${relativePath}`;
  }
  
  // Default: assume it's a direct path relative to the API
  // Don't add /workspace/ prefix as it might already include the correct path structure
  console.log(`⚠️ Unknown file path format: ${filePath}`);
  return `${API_BASE_URL}/${filePath}`;
}

function createNewSession() {
  // Set new session flag and clear selected session
  isNewSession.value = true;
  selectedSession.value = null;
  // Switch to chat mode to see the empty conversation
  viewMode.value = 'chat';
}

async function handleLeftDrop(e: DragEvent) {
  isLeftDragging.value = false;
  const files = e.dataTransfer?.files;
  if (!files || files.length === 0) return;

  await handleLeftUpload(files[0]);
}

async function handleLeftUpload(file: File) {
  const form = new FormData();
  form.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: form
    });
    if (!res.ok) throw new Error('Upload failed');
    const data = await res.json();
    if (data.success) {
      uploadedFilePath.value = data.file.path;
      // Add to uploaded files history
      const fileObj = {
        name: data.file.name,
        path: data.file.path,
        absolutePath: data.file.absolutePath,
        timestamp: Date.now()
      };
      uploadedFiles.value.push(fileObj);
      console.log('✅ App.vue: File added via left sidebar:', fileObj, 'Total files:', uploadedFiles.value.length);
    }
  } catch (err) {
    console.error('Leftbar upload error', err);
  }
}

function handleLeftFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    handleLeftUpload(input.files[0]);
  }
}

function toggleView() {
  viewMode.value = viewMode.value === 'chat' ? 'viewer' : 'chat';
}

function handleViewerLoaded() {
  console.log('IFC model loaded successfully');
}

function handleViewerError(message: string) {
  console.error('Viewer error:', message);
}

function toggleLeft() {
  leftCollapsed.value = !leftCollapsed.value;
}

function toggleRight() {
  rightCollapsed.value = !rightCollapsed.value;
}

// Auto-scroll chat messages to bottom when new events arrive
watch(displayedEvents, async () => {
  await nextTick();
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }
}, { deep: true });
</script>

<template>
  <div class="min-h-screen theme-bg flex flex-col transition-colors duration-300">
    <!-- Main App (only shown when authenticated) -->
    <template v-if="isAuthenticated">
    <!-- Header -->
    <header class="gradient-header px-6 py-4 flex items-center justify-between shadow-lg">
      <div class="flex items-center gap-4">
        <img :src="BimaiLogo" alt="BIM AI" class="h-12" />
      </div>

      <div class="flex items-center gap-6">
        <!-- View Toggle -->
        <div class="flex items-center gap-2 bg-white/10 rounded-lg p-1">
          <button
            @click="viewMode = 'chat'"
            class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'chat'
              ? 'bg-buildos-primary text-white'
              : 'text-white/70 hover:text-white'"
          >
            💬 Chat
          </button>
          <button
            v-if="uploadedFilePath"
            @click="viewMode = 'viewer'"
            class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'viewer'
              ? 'bg-buildos-primary text-white'
              : 'text-white/70 hover:text-white'"
          >
            🏗️ 3D Viewer
          </button>
          <button
            @click="viewMode = 'tools'"
            class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'tools'
              ? 'bg-buildos-primary text-white'
              : 'text-white/70 hover:text-white'"
          >
            🛠️ Tools
          </button>
        </div>

        <!-- Stats -->
        <div class="flex gap-4 text-sm text-white/80">
          <span>{{ stats.totalEvents }} events</span>
          <span>{{ stats.sessions }} sessions</span>
        </div>

        <!-- Connection status -->
        <div class="flex items-center gap-2">
          <div
            class="w-2 h-2 rounded-full"
            :class="isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'"
          ></div>
          <span class="text-sm text-white/80">
            {{ isConnected ? 'Connected' : 'Disconnected' }}
          </span>
        </div>

        <!-- API Key indicator & settings -->
        <button
          @click="showApiKeyModal = true"
          class="flex items-center gap-2 px-3 py-1 rounded-lg transition-colors"
          :class="apiKey ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' : 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'"
          :title="apiKey ? 'API Key configured - Click to change' : 'Click to set your Anthropic API Key'"
        >
          <span>🔑</span>
          <span class="text-sm">{{ apiKey ? 'API Key ✓' : 'Set API Key' }}</span>
        </button>

        <!-- Toggle timeline -->
        <button
          @click="showTimeline = !showTimeline"
          class="text-white/80 hover:text-white transition-colors"
          :title="showTimeline ? 'Hide timeline' : 'Show timeline'"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- Theme Toggle -->
        <button
          @click="toggleTheme"
          class="theme-toggle"
          :title="theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          <div class="theme-toggle-knob">
            {{ theme === 'dark' ? '🌙' : '☀️' }}
          </div>
        </button>
      </div>
    </header>

    <!-- Main content -->
    <main class="flex-1 flex overflow-hidden">
      <!-- Left sidebar: Sessions -->
      <aside
        :class="[leftCollapsed ? 'w-12' : 'w-64', 'theme-surface theme-border border-r overflow-y-auto p-3 transition-all flex flex-col']"
        @dragover.prevent="isLeftDragging = true"
        @dragleave="isLeftDragging = false"
        @drop.prevent="handleLeftDrop"
      >
        <!-- Collapsed state: Just expand button -->
        <div v-if="leftCollapsed" class="flex flex-col items-center">
          <button @click="toggleLeft" class="theme-text-secondary hover:theme-text p-2 rotate-180" title="Expand">
            ⇤
          </button>
        </div>

        <!-- Expanded state: Full content -->
        <template v-else>
          <div :class="['flex items-center justify-between mb-3', isLeftDragging ? 'ring-2 ring-buildos-primary/40' : '']">
            <h2 class="text-sm font-medium theme-text-secondary">Sessions</h2>
            <button @click="toggleLeft" class="theme-text-secondary hover:theme-text" title="Collapse">⇤</button>
          </div>

          <!-- New Session Button -->
          <button
            @click="createNewSession"
            class="w-full mb-3 px-3 py-2 bg-buildos-primary hover:bg-buildos-secondary text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span>➕</span>
            <span>New Session</span>
          </button>

          <SessionFilter
            :events="events"
            :selected-session="selectedSession"
            @select="handleSessionSelect"
          />

          <!-- Left sidebar dropzone (below sessions) -->
          <div class="mt-3">
            <div
              class="mx-0 mb-2 border-2 border-dashed theme-border rounded-lg p-3 text-center cursor-pointer transition-colors"
              :class="{ 'border-buildos-primary bg-buildos-primary/10': isLeftDragging }"
              @dragover.prevent="isLeftDragging = true"
              @dragleave="isLeftDragging = false"
              @drop.prevent="handleLeftDrop"
              @click="(leftFileInput as HTMLInputElement).click()"
            >
              <p class="text-sm theme-text-secondary">
                Drop IFC file here to upload for viewer or <span class="text-buildos-primary">browse</span>
              </p>
            </div>
            <input ref="leftFileInput" type="file" class="hidden" accept=".ifc,.csv,.xlsx" @change="handleLeftFileSelect" />
          </div>

          <!-- File info when uploaded -->
          <div v-if="uploadedFilePath" class="mt-6 pt-4 border-t theme-border">
            <h2 class="text-sm font-medium theme-text-secondary mb-3">Current File</h2>
            <div class="theme-bg rounded-lg p-3">
              <div class="flex items-center gap-2 text-sm">
                <span class="text-buildos-primary">📄</span>
                <span class="theme-text truncate">
                  {{ uploadedFilePath.split('/').pop() }}
                </span>
              </div>
              <button
                @click="viewMode = 'viewer'"
                class="mt-2 w-full text-xs text-buildos-primary hover:text-buildos-secondary transition-colors"
              >
                View in 3D →
              </button>
            </div>
          </div>

          <!-- All Uploaded Files -->
          <div v-if="uploadedFiles.length > 0" class="mt-6 pt-4 border-t theme-border">
            <h2 class="text-sm font-medium theme-text-secondary mb-3">Loaded Files ({{ uploadedFiles.length }})</h2>
            <div class="space-y-2 max-h-48 overflow-y-auto">
              <div
                v-for="file in uploadedFiles"
                :key="file.timestamp"
                class="theme-bg rounded-lg p-2 theme-surface-hover transition-colors cursor-pointer"
                @click="uploadedFilePath = file.path"
              >
                <div class="flex items-center gap-2 text-sm">
                  <span class="text-buildos-primary text-xs">📄</span>
                  <span class="theme-text text-xs truncate flex-1">
                    {{ file.name }}
                  </span>
                </div>
                <div class="text-xs theme-text-muted mt-1">
                  {{ new Date(file.timestamp).toLocaleTimeString() }}
                </div>
              </div>
            </div>
            <p class="text-xs theme-text-muted mt-2 italic">
              All files available to orchestrator
            </p>
          </div>
        </template>
      </aside>

      <!-- Center: Agent Flow, Content Area, and Chat -->
      <div class="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
        <!-- Agent Flow Tree (visible in chat/viewer modes) -->
        <AgentFlowTree
          v-show="viewMode !== 'tools'"
          :events="displayedEvents"
          @nodeClick="handleFlowNodeClick"
        />

        <!-- Content area - Toggle between Chat Messages and 3D Viewer -->
        <div class="flex-1 min-h-0 relative">
          <!-- Chat Messages View (scrollable history) -->
          <div ref="chatMessagesRef" v-show="viewMode === 'chat'" class="absolute inset-0 overflow-y-auto p-3 space-y-3 theme-surface rounded-lg">
            <!-- Session events -->
            <div v-for="event in displayedEvents" :key="event.id" :data-event-id="event.id" class="text-sm transition-all duration-300">
              <!-- User message -->
              <div v-if="event.hook_event_type === 'UserPromptSubmit'" class="flex justify-end">
                <div class="bg-buildos-primary text-white rounded-lg px-3 py-2 max-w-[80%]">
                  {{ event.payload.prompt }}
                </div>
              </div>

              <!-- Agent thinking -->
              <div v-else-if="event.hook_event_type === 'AgentThinking'" class="flex">
                <div class="theme-surface theme-border border rounded-lg px-3 py-2 max-w-[80%]">
                  <span class="text-xs theme-text-muted block mb-1">🧠 Thinking</span>
                  <span class="theme-text">{{ String(event.payload.thought).slice(0, 200) }}</span>
                </div>
              </div>

              <!-- Subagent start -->
              <div v-else-if="event.hook_event_type === 'SubagentStart'" class="flex">
                <div class="bg-purple-900/50 text-purple-300 rounded-lg px-3 py-2">
                  <span class="text-xs block mb-1">👥 Starting agent: {{ event.payload.agent_type }}</span>
                  {{ event.payload.description }}
                </div>
              </div>

              <!-- Final answer -->
              <div v-else-if="event.hook_event_type === 'Stop' && event.payload.status === 'success'" class="flex">
                <div class="bg-green-900/50 text-green-300 rounded-lg px-4 py-3 max-w-[90%] w-full">
                  <span class="text-xs text-green-500 block mb-2">✅ Complete</span>
                  <MarkdownRenderer :content="String(event.payload.message)" />
                  <!-- Downloadable Files -->
                  <div v-if="extractDownloadableFiles(String(event.payload.message)).length > 0" class="mt-4 pt-3 border-t border-green-700/50">
                    <div class="flex flex-wrap gap-2">
                      <a
                        v-for="(file, index) in extractDownloadableFiles(String(event.payload.message))"
                        :key="index"
                        :href="getDownloadUrl(file.path)"
                        target="_blank"
                        download
                        class="inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                        :class="{
                          'bg-green-600 hover:bg-green-500 text-white': file.type === 'pdf',
                          'bg-emerald-600 hover:bg-emerald-500 text-white': file.type === 'excel',
                          'bg-orange-600 hover:bg-orange-500 text-white': file.type === 'pptx',
                          'bg-blue-600 hover:bg-blue-500 text-white': file.type === 'docx'
                        }"
                      >
                        <svg v-if="file.type === 'pdf'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <svg v-else-if="file.type === 'excel'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                        </svg>
                        <svg v-else-if="file.type === 'pptx'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download {{ file.label }}
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Error -->
              <div v-else-if="event.hook_event_type === 'Stop' && event.payload.status === 'error'" class="flex">
                <div class="bg-red-900/50 text-red-300 rounded-lg px-3 py-2 max-w-[80%]">
                  <span class="text-xs text-red-500 block mb-1">❌ Error</span>
                  {{ event.payload.message }}
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="displayedEvents.length === 0" class="text-center theme-text-muted py-8">
              <p>Send a message to start</p>
              <p class="text-xs mt-2">Upload an IFC file and ask questions about it</p>
            </div>
          </div>

          <!-- 3D Viewer -->
          <div v-show="viewMode === 'viewer'" class="absolute inset-0">
            <IfcViewer
              ref="viewerRef"
              :file-path="uploadedFilePath ?? undefined"
              @loaded="handleViewerLoaded"
              @error="handleViewerError"
            />
          </div>

          <!-- Tools Builder -->
          <div v-show="viewMode === 'tools'" class="absolute inset-0">
            <ToolsBuilder />
          </div>
        </div>

        <!-- Chat Input (visible in chat/viewer modes) -->
        <ChatWindow
          v-show="viewMode !== 'tools'"
          :key="chatKey"
          :events="events"
          :compact="true"
          :available-files="uploadedFiles"
          :api-key="apiKey"
          :user-id="userId"
          :current-session-id="selectedSession"
          :is-new-session="isNewSession"
          @session-created="handleSessionCreated"
          @file-uploaded="handleFileUploaded"
        />
      </div>

      <!-- Right sidebar: Event Timeline -->
      <aside
        v-if="showTimeline"
        :class="[rightCollapsed ? 'w-12' : 'w-64', 'theme-surface theme-border border-l flex flex-col transition-all']"
      >
        <!-- Collapsed state: Just expand button -->
        <div v-if="rightCollapsed" class="flex flex-col items-center p-3">
          <button @click="toggleRight" class="theme-text-secondary hover:theme-text p-2" title="Expand">
            ⇥
          </button>
        </div>

        <!-- Expanded state: Full content -->
        <template v-else>
          <div class="p-3 border-b theme-border flex items-center justify-between">
            <h2 class="text-sm font-medium theme-text-secondary">Event Timeline</h2>
            <div class="flex items-center gap-2">
              <button @click="toggleRight" class="theme-text-secondary hover:theme-text" title="Collapse">⇥</button>
            </div>
          </div>
          <div class="flex-1 overflow-hidden">
            <EventTimeline
              :events="events"
              :selected-session="selectedSession ?? undefined"
              @toggleCollapse="toggleRight"
            />
          </div>
        </template>
      </aside>
    </main>
    </template>

    <!-- Error toast -->
    <div
      v-if="error"
      class="fixed bottom-4 right-4 bg-red-900 text-red-100 px-4 py-2 rounded-lg shadow-lg"
    >
      {{ error }}
    </div>

    <!-- API Key Login Screen (Full screen, mandatory) -->
    <div
      v-if="showApiKeyModal && !isAuthenticated"
      class="fixed inset-0 bg-gradient-to-br from-slate-100 via-white to-slate-100 flex items-center justify-center z-50"
    >
      <div class="max-w-md w-full mx-4">
        <!-- Logo/Brand -->
        <div class="text-center mb-8">
          <img :src="BimaiLogo" alt="BIM AI" class="h-20 mx-auto mb-4" />
        </div>

        <!-- Login Card -->
        <div class="bg-white/80 backdrop-blur border border-slate-200 rounded-2xl p-8 shadow-xl">
          <h2 class="text-xl font-semibold text-slate-800 mb-2">Enter your API Key</h2>
          <p class="text-slate-500 text-sm mb-6">
            Your Anthropic API key is used to access Claude AI.
            Get one at <a href="https://console.anthropic.com/" target="_blank" class="text-blue-600 hover:text-blue-500 underline">console.anthropic.com</a>
          </p>

          <!-- Error Message -->
          <div v-if="apiKeyError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-600 text-sm">{{ apiKeyError }}</p>
          </div>

          <!-- Input -->
          <input
            v-model="apiKeyInput"
            type="password"
            placeholder="sk-ant-api03-..."
            class="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 mb-4"
            @keyup.enter="saveApiKey"
            autofocus
          />

          <!-- Submit Button -->
          <button
            @click="saveApiKey"
            :disabled="isValidatingKey"
            class="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-400 font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            style="color: white;"
          >
            <span v-if="isValidatingKey" style="color: white;">Validating...</span>
            <span v-else style="color: white;">Continue</span>
          </button>

          <!-- Security Note -->
          <div class="mt-6 p-3 bg-slate-50 rounded-lg">
            <p class="text-slate-500 text-xs flex items-start gap-2">
              <span class="text-green-500">🔒</span>
              <span>Your API key is stored only in your browser. Each user's sessions are completely isolated.</span>
            </p>
          </div>
        </div>

        <!-- Footer -->
        <p class="text-center text-slate-400 text-xs mt-6">
          Powered by Claude AI
        </p>
      </div>
    </div>

    <!-- API Key Settings Modal (when already authenticated) -->
    <div
      v-if="showApiKeyModal && isAuthenticated"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="theme-surface theme-border border rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
        <h3 class="text-xl font-bold theme-text mb-4">API Key Settings</h3>

        <div class="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p class="text-green-400 text-sm">API Key is configured</p>
          <p class="theme-text-muted text-xs mt-1">Key: {{ apiKey.slice(0, 10) }}...{{ apiKey.slice(-4) }}</p>
          <p class="theme-text-muted text-xs mt-1">User ID: {{ userId }}</p>
        </div>

        <p class="theme-text-secondary text-sm mb-4">
          Enter a new key to switch accounts, or clear to log out.
        </p>

        <input
          v-model="apiKeyInput"
          type="password"
          placeholder="Enter new API key..."
          class="input-field w-full mb-4"
        />

        <div v-if="apiKeyError" class="mb-4 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p class="text-red-400 text-sm">{{ apiKeyError }}</p>
        </div>

        <div class="flex gap-3">
          <button
            @click="saveApiKey"
            :disabled="!apiKeyInput"
            class="flex-1 px-4 py-2 bg-buildos-primary hover:bg-buildos-secondary disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            Update Key
          </button>
          <button
            @click="clearApiKey"
            class="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg transition-colors"
          >
            Log Out
          </button>
          <button
            @click="showApiKeyModal = false"
            class="px-4 py-2 theme-surface theme-border border hover:opacity-80 theme-text font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
