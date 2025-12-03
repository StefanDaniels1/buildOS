<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import type { HookEvent } from '../types';
import { API_BASE_URL } from '../config';

const props = defineProps<{
  events: HookEvent[];
  initialMessage?: string | null;
  compact?: boolean; // New prop for compact mode (input only)
  availableFiles?: Array<{ name: string; path: string; absolutePath: string; timestamp: number }>; // All uploaded files
  apiKey?: string; // User-provided Anthropic API key
}>();

const emit = defineEmits<{
  (e: 'sessionCreated', sessionId: string): void;
  (e: 'fileUploaded', file: {name: string, path: string, absolutePath: string, timestamp: number}): void;
  (e: 'initialConsumed'): void;
}>();

const message = ref('');
const isLoading = ref(false);
const sessionId = ref(generateSessionId());
const uploadedFile = ref<{ name: string; path: string; absolutePath: string } | null>(null);
const chatRef = ref<HTMLElement | null>(null);
const isDragging = ref(false);

// Filter events for current session
const sessionEvents = computed(() => {
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

  // DEBUG: Log context
  console.log('📤 SENDING MESSAGE');
  console.log('🔍 availableFiles length:', props.availableFiles?.length || 0);
  console.log('🔑 Has API key:', !!props.apiKey);

  const payload = {
    message: userMessage,
    session_id: sessionId.value,
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

    emit('sessionCreated', sessionId.value);
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
  sessionId.value = generateSessionId();
  uploadedFile.value = null;
  message.value = '';
}

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
    <div class="p-3 border-b border-gray-700 flex justify-between items-center">
      <div>
        <h3 class="font-medium">Chat</h3>
        <span class="text-xs text-gray-500">{{ sessionId.slice(0, 16) }}...</span>
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
          <div class="bg-gray-700 text-gray-300 rounded-lg px-3 py-2 max-w-[80%]">
            <span class="text-xs text-gray-500 block mb-1">🧠 Thinking</span>
            {{ String(event.payload.thought).slice(0, 200) }}
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

      <!-- Loading indicator -->
      <div v-if="isRunning" class="flex items-center gap-2 text-gray-400">
        <div class="animate-pulse flex gap-1">
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 0ms"></div>
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 150ms"></div>
          <div class="w-2 h-2 bg-buildos-primary rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
        <span class="text-sm">Processing...</span>
      </div>

      <!-- Empty state -->
      <div v-if="sessionEvents.length === 0" class="text-center text-gray-500 py-8">
        <p>Send a message to start</p>
        <p class="text-xs mt-2">Upload an IFC file and ask questions about it</p>
      </div>
    </div>

    <!-- Input area -->
    <div class="p-3 border-t border-gray-700">
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
  </div>
</template>
