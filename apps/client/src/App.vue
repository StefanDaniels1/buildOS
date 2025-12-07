<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useWebSocket } from './composables/useWebSocket';
import { useTheme } from './composables/useTheme';
import LiveChart from './components/LiveChart.vue';
import ChatWindow from './components/ChatWindow.vue';
import EventTimeline from './components/EventTimeline.vue';
import SessionFilter from './components/SessionFilter.vue';
import IfcViewer from './components/IfcViewer.vue';
import { API_BASE_URL } from './config';

const { events, isConnected, error } = useWebSocket();
const { theme, toggleTheme } = useTheme();

const selectedSession = ref<string | null>(null);
const showTimeline = ref(true);
const leftCollapsed = ref(false);
const rightCollapsed = ref(false);
const isLeftDragging = ref(false);
const leftFileInput = ref<HTMLInputElement | null>(null);
const isNewSession = ref(false); // Flag to track new session creation

// View mode: 'chat' or 'viewer'
type ViewMode = 'chat' | 'viewer';
const viewMode = ref<ViewMode>('chat');

// Track uploaded file for viewer
const uploadedFilePath = ref<string | null>(null);
const viewerRef = ref<InstanceType<typeof IfcViewer> | null>(null);

// Track all uploaded files (history)
const uploadedFiles = ref<Array<{ name: string; path: string; absolutePath: string; timestamp: number }>>([]);

// API Key management
const apiKey = ref('');
const showApiKeyModal = ref(false);
const apiKeyInput = ref('');

// Load API key from localStorage on mount
onMounted(() => {
  const savedKey = localStorage.getItem('anthropic_api_key');
  if (savedKey) {
    apiKey.value = savedKey;
  }
});

function saveApiKey() {
  apiKey.value = apiKeyInput.value.trim();
  if (apiKey.value) {
    localStorage.setItem('anthropic_api_key', apiKey.value);
  } else {
    localStorage.removeItem('anthropic_api_key');
  }
  showApiKeyModal.value = false;
  apiKeyInput.value = '';
}

function clearApiKey() {
  apiKey.value = '';
  localStorage.removeItem('anthropic_api_key');
  showApiKeyModal.value = false;
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
</script>

<template>
  <div class="min-h-screen theme-bg flex flex-col transition-colors duration-300">
    <!-- Header -->
    <header class="gradient-header px-6 py-4 flex items-center justify-between shadow-lg">
      <div class="flex items-center gap-4">
        <h1 class="text-xl font-bold text-white">buildOS Dashboard</h1>
        <span class="text-xs text-white/70">Multi-Agent Observability</span>
      </div>

      <div class="flex items-center gap-6">
        <!-- View Toggle (only show when file is uploaded) -->
        <div v-if="uploadedFilePath" class="flex items-center gap-2 bg-white/10 rounded-lg p-1">
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
            @click="viewMode = 'viewer'"
            class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'viewer'
              ? 'bg-buildos-primary text-white'
              : 'text-white/70 hover:text-white'"
          >
            🏗️ 3D Viewer
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

      <!-- Center: Chart, Content Area, and Chat -->
      <div class="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
        <!-- Chart (always visible) -->
        <LiveChart :events="events" />

        <!-- Content area - Toggle between Chat Messages and 3D Viewer -->
        <div class="flex-1 min-h-0 relative">
          <!-- Chat Messages View (scrollable history) -->
          <div v-show="viewMode === 'chat'" class="absolute inset-0 overflow-y-auto p-3 space-y-3 theme-surface rounded-lg">
            <!-- Session events -->
            <div v-for="event in displayedEvents" :key="event.id" class="text-sm">
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
                <div class="bg-green-900/50 text-green-300 rounded-lg px-3 py-2 max-w-[80%]">
                  <span class="text-xs text-green-500 block mb-1">✅ Complete</span>
                  {{ event.payload.message }}
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
        </div>

        <!-- Chat Input (always visible at bottom) -->
        <ChatWindow
          :key="chatKey"
          :events="events"
          :compact="true"
          :available-files="uploadedFiles"
          :api-key="apiKey"
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

    <!-- Error toast -->
    <div
      v-if="error"
      class="fixed bottom-4 right-4 bg-red-900 text-red-100 px-4 py-2 rounded-lg shadow-lg"
    >
      {{ error }}
    </div>

    <!-- API Key Modal -->
    <div
      v-if="showApiKeyModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showApiKeyModal = false"
    >
      <div class="theme-surface theme-border border rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
        <h3 class="text-xl font-bold theme-text mb-4">🔑 Anthropic API Key</h3>
        
        <p class="theme-text-secondary text-sm mb-4">
          Enter your Anthropic API key to use the AI features. 
          Get one at <a href="https://console.anthropic.com/" target="_blank" class="text-buildos-primary hover:underline">console.anthropic.com</a>
        </p>

        <div v-if="apiKey" class="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p class="text-green-400 text-sm">✓ API Key is configured</p>
          <p class="theme-text-muted text-xs mt-1">Key: {{ apiKey.slice(0, 10) }}...{{ apiKey.slice(-4) }}</p>
        </div>

        <input
          v-model="apiKeyInput"
          type="password"
          placeholder="sk-ant-api03-..."
          class="input-field w-full mb-4"
        />

        <div class="flex gap-3">
          <button
            @click="saveApiKey"
            class="flex-1 px-4 py-2 bg-buildos-primary hover:bg-buildos-secondary text-white font-medium rounded-lg transition-colors"
          >
            Save Key
          </button>
          <button
            v-if="apiKey"
            @click="clearApiKey"
            class="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg transition-colors"
          >
            Clear
          </button>
          <button
            @click="showApiKeyModal = false"
            class="px-4 py-2 theme-surface theme-border border hover:opacity-80 theme-text font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>

        <p class="theme-text-muted text-xs mt-4">
          Your API key is stored locally in your browser and never sent to our servers.
        </p>
      </div>
    </div>
  </div>
</template>
