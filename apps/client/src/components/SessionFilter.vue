<script setup lang="ts">
import { computed, ref } from 'vue';
import type { HookEvent } from '../types';
import { useEventColors } from '../composables/useEventColors';
import { API_BASE_URL } from '../config';

const props = defineProps<{
  events: HookEvent[];
  selectedSession: string | null;
}>();

const emit = defineEmits<{
  (e: 'select', sessionId: string | null): void;
  (e: 'cleared'): void;
}>();

const { getSessionColor } = useEventColors();
const isClearing = ref(false);

// Get unique sessions with counts
const sessions = computed(() => {
  const sessionMap = new Map<string, { count: number; lastEvent: number }>();

  for (const event of props.events) {
    const existing = sessionMap.get(event.session_id);
    if (existing) {
      existing.count++;
      existing.lastEvent = Math.max(existing.lastEvent, event.timestamp || 0);
    } else {
      sessionMap.set(event.session_id, {
        count: 1,
        lastEvent: event.timestamp || 0
      });
    }
  }

  return Array.from(sessionMap.entries())
    .map(([id, data]) => ({
      id,
      count: data.count,
      lastEvent: data.lastEvent,
      color: getSessionColor(id)
    }))
    .sort((a, b) => b.lastEvent - a.lastEvent);
});

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function clearAllSessions() {
  if (!confirm('Clear all sessions? This cannot be undone.')) return;
  
  isClearing.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/events`, {
      method: 'DELETE'
    });
    if (response.ok) {
      emit('cleared');
      // Reload page to reset state
      window.location.reload();
    }
  } catch (error) {
    console.error('Failed to clear sessions:', error);
  } finally {
    isClearing.value = false;
  }
}
</script>

<template>
  <div class="space-y-1">
    <!-- All sessions button -->
    <button
      @click="emit('select', null)"
      class="w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
      :class="selectedSession === null
        ? 'bg-buildos-primary text-white'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
    >
      <span class="w-2 h-2 rounded-full bg-gray-400"></span>
      <span class="flex-1 text-left text-sm">All Sessions</span>
      <span class="text-xs opacity-70">{{ events.length }}</span>
    </button>

    <!-- Session list -->
    <button
      v-for="session in sessions"
      :key="session.id"
      @click="emit('select', session.id)"
      class="w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
      :class="selectedSession === session.id
        ? 'bg-buildos-primary text-white'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
    >
      <span
        class="w-2 h-2 rounded-full flex-shrink-0"
        :style="{ backgroundColor: session.color }"
      ></span>
      <span class="flex-1 text-left text-sm truncate font-mono">
        {{ session.id.slice(0, 12) }}...
      </span>
      <span class="text-xs opacity-70">{{ session.count }}</span>
    </button>

    <div v-if="sessions.length === 0" class="text-center text-gray-500 py-4 text-sm">
      No sessions yet
    </div>

    <!-- Clear all button -->
    <button
      v-if="sessions.length > 0"
      @click="clearAllSessions"
      :disabled="isClearing"
      class="w-full mt-2 px-3 py-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors border border-red-900/30"
    >
      {{ isClearing ? 'Clearing...' : '🗑️ Clear All Sessions' }}
    </button>
  </div>
</template>
