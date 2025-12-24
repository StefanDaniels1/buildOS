<script setup lang="ts">
import { computed } from 'vue';
import type { CustomTool } from '../composables/useTools';

const props = defineProps<{
  tools: CustomTool[];
  selectedId: number | null;
}>();

const emit = defineEmits<{
  (e: 'select', id: number): void;
  (e: 'toggle', id: number): void;
  (e: 'delete', id: number): void;
}>();

function formatDate(timestamp?: number): string {
  if (!timestamp) return '';
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function handleToggle(e: Event, id: number) {
  e.stopPropagation();
  emit('toggle', id);
}

function handleDelete(e: Event, id: number) {
  e.stopPropagation();
  if (confirm('Delete this tool? This cannot be undone.')) {
    emit('delete', id);
  }
}
</script>

<template>
  <div class="space-y-2">
    <div
      v-for="tool in tools"
      :key="tool.id"
      class="p-3 rounded-lg border cursor-pointer transition-all"
      :class="[
        selectedId === tool.id
          ? 'border-buildos-primary bg-buildos-primary/10'
          : 'theme-border theme-surface hover:border-buildos-primary/50'
      ]"
      @click="emit('select', tool.id!)"
    >
      <div class="flex items-start justify-between gap-3">
        <!-- Tool info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="font-mono text-sm font-medium theme-text truncate">
              {{ tool.name }}
            </span>
            <span
              v-if="tool.enabled"
              class="px-1.5 py-0.5 text-xs rounded bg-green-500/20 text-green-400"
            >
              Active
            </span>
          </div>
          <p class="text-xs theme-text-muted mt-1 line-clamp-2">
            {{ tool.description }}
          </p>
          <div class="flex items-center gap-3 mt-2 text-xs theme-text-muted">
            <span v-if="Object.keys(tool.input_schema).length > 0">
              {{ Object.keys(tool.input_schema).length }} params
            </span>
            <span v-if="Object.keys(tool.env_vars || {}).length > 0">
              {{ Object.keys(tool.env_vars).length }} env vars
            </span>
            <span v-if="tool.updated_at">
              {{ formatDate(tool.updated_at) }}
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <!-- Toggle switch -->
          <button
            @click="handleToggle($event, tool.id!)"
            class="relative w-10 h-5 rounded-full transition-colors"
            :class="tool.enabled ? 'bg-green-500' : 'bg-gray-600'"
            :title="tool.enabled ? 'Disable tool' : 'Enable tool'"
          >
            <span
              class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
              :class="tool.enabled ? 'left-5' : 'left-0.5'"
            ></span>
          </button>

          <!-- Delete button -->
          <button
            @click="handleDelete($event, tool.id!)"
            class="p-1.5 rounded text-red-400 hover:bg-red-500/20 transition-colors"
            title="Delete tool"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="tools.length === 0" class="text-center py-8 theme-text-muted">
      <p>No custom tools yet</p>
      <p class="text-xs mt-1">Create a tool to extend the orchestrator's capabilities</p>
    </div>
  </div>
</template>
