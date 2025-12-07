<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import type { HookEvent } from '../types';
import { API_BASE_URL } from '../config';
import MarkdownRenderer from './MarkdownRenderer.vue';

const props = defineProps<{
  events: HookEvent[];
  initialMessage?: string | null;
  compact?: boolean; // New prop for compact mode (input only)
  availableFiles?: Array<{ name: string; path: string; absolutePath: string; timestamp: number }>; // All uploaded files
  apiKey?: string; // User-provided Anthropic API key
  currentSessionId?: string | null; // Session ID from parent to continue conversation
  isNewSession?: boolean; // Flag to indicate a new session should be created
}>();

const emit = defineEmits<{
  (e: 'sessionCreated', sessionId: string): void;
  (e: 'fileUploaded', file: {name: string, path: string, absolutePath: string, timestamp: number}): void;
  (e: 'initialConsumed'): void;
}>();

const message = ref('');
const isLoading = ref(false);
const internalSessionId = ref<string | null>(null);
const uploadedFile = ref<{ name: string; path: string; absolutePath: string } | null>(null);
const chatRef = ref<HTMLElement | null>(null);
const isDragging = ref(false);

// Compute the active session ID - use parent's session or internal one
const sessionId = computed(() => {
  // If we have an internal session ID (from new session creation), use it
  if (internalSessionId.value) {
    return internalSessionId.value;
  }
  // If parent passed a current session, use it to continue the conversation
  if (props.currentSessionId) {
    return props.currentSessionId;
  }
  // No session yet - will be created on first message
  return null;
});

// Filter events for current session
const sessionEvents = computed(() => {
  if (!sessionId.value) return [];
  return props.events.filter(e => e.session_id === sessionId.value);
});

// DEBUG: Watch availableFiles changes
watch(() => props.availableFiles, (newFiles) => {
  console.log('🔍 ChatWindow: availableFiles prop changed:', newFiles);
}, { immediate: true, deep: true });

// Get the final answer from Stop event
const finalAnswer = computed(() => {
  const stopEvent = sessionEvents.value.find(e =>
    e.hook_event_type === 'Stop' && e.payload.status === 'success'
  );
  return stopEvent?.payload.message as string || null;
});

// Check if orchestrator is running
const isRunning = computed(() => {
  const hasStart = sessionEvents.value.some(e => e.hook_event_type === 'SessionStart');
  const hasEnd = sessionEvents.value.some(e => e.hook_event_type === 'SessionEnd' || e.hook_event_type === 'Stop');
  return hasStart && !hasEnd;
});

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

// Get or create session ID for sending messages
function getActiveSessionId(): string {
  // If we already have an active session, use it
  if (sessionId.value) {
    return sessionId.value;
  }
  // Create a new session ID
  const newId = generateSessionId();
  internalSessionId.value = newId;
  return newId;
}

async function sendMessage() {
  const trimmed = message.value.trim();
  if (!trimmed || isLoading.value) return;

  // Prevent accidental single-character sends
  if (trimmed.length < 2) {
    console.log('Message too short, ignoring');
    return;
  }

  isLoading.value = true;
  const userMessage = trimmed;
  message.value = '';

  // Get or create the session ID
  const activeSessionId = getActiveSessionId();

  // DEBUG: Log context
  console.log('📤 SENDING MESSAGE');
  console.log('🔍 Session ID:', activeSessionId);
  console.log('🔍 availableFiles length:', props.availableFiles?.length || 0);
  console.log('🔑 Has API key:', !!props.apiKey);

  const payload = {
    message: userMessage,
    session_id: activeSessionId,
    file_path: uploadedFile.value?.absolutePath,
    available_files: props.availableFiles?.map(f => f.absolutePath) || [],
    api_key: props.apiKey || undefined
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    
    if (!response.ok) {
      alert(data.error || 'Failed to send message');
      throw new Error(data.error || 'Failed to send message');
    }

    emit('sessionCreated', activeSessionId);
  } catch (error) {
    console.error('Error sending message:', error);
  } finally {
    isLoading.value = false;
  }
}

async function handleFileUpload(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) throw new Error('Upload failed');

    const data = await response.json();
    if (data.success) {
      uploadedFile.value = {
        name: data.file.name,
        path: data.file.path,
        absolutePath: data.file.absolutePath
      };
      // Emit full file object for parent to track
      emit('fileUploaded', {
        name: data.file.name,
        path: data.file.path,
        absolutePath: data.file.absolutePath,
        timestamp: Date.now()
      });
    }
  } catch (error) {
    console.error('Upload error:', error);
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFileUpload(files[0]);
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    handleFileUpload(input.files[0]);
  }
}

function clearFile() {
  uploadedFile.value = null;
}

function newSession() {
  internalSessionId.value = generateSessionId();
  uploadedFile.value = null;
  message.value = '';
}

// Reset internal session when parent signals a new session via key change
watch(() => props.isNewSession, (isNew) => {
  if (isNew) {
    internalSessionId.value = null;
  }
});

// Also reset when currentSessionId changes (switching sessions)
watch(() => props.currentSessionId, () => {
  // Clear internal session to use the parent's session
  internalSessionId.value = null;
});

// Auto-scroll chat
watch(sessionEvents, async () => {
  await nextTick();
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight;
  }
}, { deep: true });

// Populate input when initialMessage provided, but DON'T auto-send
watch(() => props.initialMessage, async (val) => {
  if (val && val.trim()) {
    // Just populate the input field, let user send manually
    message.value = val;
    await nextTick();
    emit('initialConsumed');
  }
});
</script>

<template>
  <div v-if="compact" class="card p-3">
    <!-- Compact mode: input only -->
    <form @submit.prevent="sendMessage" class="flex gap-2">
      <input
        v-model="message"
        type="text"
        placeholder="Ask about your IFC model..."
        class="input-field flex-1"
      />
      <button type="button" @click="($refs.fileInput as HTMLInputElement).click()" class="text-gray-300 px-2" title="Attach file">📎</button>
      <button
        type="submit"
        class="btn-primary"
        :disabled="isLoading || message.trim().length < 2"
      >
        Send
      </button>
    </form>
    <!-- hidden persistent file input -->
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      accept=".ifc,.csv,.xlsx"
      @change="handleFileSelect"
    />
  </div>

  <div v-else class="card flex flex-col h-full">
    <!-- Header -->
    <div class="p-3 border-b theme-border flex justify-between items-center">
      <div>
        <h3 class="font-medium theme-text">Chat</h3>
        <span class="text-xs theme-text-muted">{{ sessionId ? sessionId.slice(0, 16) + '...' : 'New Session' }}</span>
      </div>
      <button
        @click="newSession"
        class="text-xs text-buildos-primary hover:text-buildos-secondary"
      >
        New Session
      </button>
    </div>

    <!-- Chat messages -->
    <div
      ref="chatRef"
      class="flex-1 overflow-y-auto p-3 space-y-3"
    >
      <!-- Session events -->
      <div v-for="event in sessionEvents" :key="event.id" class="text-sm">
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

      <!-- Loading indicator -->
      <div v-if="isRunning" class="flex items-center gap-2 theme-text-secondary">
        <div class="animate-pulse flex gap-1">
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 0ms"></div>
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 150ms"></div>
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
        <span class="text-sm">Processing...</span>
      </div>

      <!-- Empty state -->
      <div v-if="sessionEvents.length === 0" class="text-center theme-text-muted py-8">
        <p>Send a message to start</p>
        <p class="text-xs mt-2">Upload an IFC file and ask questions about it</p>
      </div>
    </div>

    <!-- Input area -->
    <div class="p-3 border-t theme-border">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          v-model="message"
          type="text"
          placeholder="Ask about your IFC model..."
          class="input-field flex-1"
        />
        <button type="button" @click="($refs.fileInput as HTMLInputElement).click()" class="theme-text-secondary px-2" title="Attach file">📎</button>
        <button
          type="submit"
          class="btn-primary"
          :disabled="isLoading || message.trim().length < 2"
        >
          Send
        </button>
      </form>
      <!-- hidden persistent file input -->
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept=".ifc,.csv,.xlsx"
        @change="handleFileSelect"
      />
    </div>
  </div>
</template>
