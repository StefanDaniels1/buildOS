<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue';
import type { HookEvent } from '../types';
import EventRow from './EventRow.vue';

const props = defineProps<{
  events: HookEvent[];
  selectedSession?: string;
}>();

const emit = defineEmits<{
  (e: 'toggleCollapse'): void;
}>();

const searchQuery = ref('');
const autoScroll = ref(true);
const timelineRef = ref<HTMLElement | null>(null);

const filteredEvents = computed(() => {
  let filtered = props.events;

  // Filter by session
  if (props.selectedSession) {
    filtered = filtered.filter(e => e.session_id === props.selectedSession);
  }

  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(e =>
      e.hook_event_type.toLowerCase().includes(query) ||
      JSON.stringify(e.payload).toLowerCase().includes(query) ||
      e.session_id.toLowerCase().includes(query)
    );
  }

  return filtered;
});

// Auto-scroll when new events arrive
watch(() => props.events.length, async () => {
  if (autoScroll.value && timelineRef.value) {
    await nextTick();
    timelineRef.value.scrollTop = timelineRef.value.scrollHeight;
  }
});

</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Search bar -->
    <div class="p-3 border-b theme-border flex items-center justify-between">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search events..."
        class="input-field w-2/3 text-sm"
      />
      <div class="flex items-center gap-2">
        <label class="flex items-center gap-1 cursor-pointer text-xs theme-text-secondary">
          <input
            type="checkbox"
            v-model="autoScroll"
            class="rounded"
          />
          Auto-scroll
        </label>
        <button @click="$emit('toggleCollapse')" class="theme-text-secondary hover:theme-text text-sm">⇔</button>
      </div>
    </div>

    <!-- Event list -->
    <div
      ref="timelineRef"
      class="flex-1 overflow-y-auto p-2 space-y-1 h-full"
      style="max-height: calc(100vh - 200px);"
    >
      <EventRow
        v-for="event in filteredEvents"
        :key="event.id"
        :event="event"
      />

      <div v-if="filteredEvents.length === 0" class="text-center theme-text-muted py-8">
        No events yet
      </div>
    </div>

    <!-- Footer -->
    <div class="p-2 border-t theme-border flex justify-between items-center text-xs theme-text-secondary">
      <span>{{ filteredEvents.length }} events</span>
      <label class="flex items-center gap-1 cursor-pointer">
      </label>
    </div>
  </div>
</template>
