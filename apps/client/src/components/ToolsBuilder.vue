<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useTools } from '../composables/useTools';
import type { CustomTool } from '../composables/useTools';
import ToolsList from './ToolsList.vue';
import ToolEditor from './ToolEditor.vue';

const {
  tools,
  templates,
  isLoading,
  error,
  enabledCount,
  toolCount,
  fetchTools,
  fetchTemplates,
  createTool,
  updateTool,
  deleteTool,
  toggleTool,
  getToolById,
  clearError
} = useTools();

// UI State
const selectedToolId = ref<number | null>(null);
const showEditor = ref(false);
const isCreating = ref(false);

// Selected tool
const selectedTool = computed(() => {
  if (!selectedToolId.value) return null;
  return getToolById(selectedToolId.value) || null;
});

// Load data on mount
onMounted(async () => {
  await Promise.all([fetchTools(), fetchTemplates()]);
});

function handleSelectTool(id: number) {
  selectedToolId.value = id;
  showEditor.value = true;
  isCreating.value = false;
}

function handleCreateNew() {
  selectedToolId.value = null;
  showEditor.value = true;
  isCreating.value = true;
}

async function handleToggleTool(id: number) {
  await toggleTool(id);
}

async function handleDeleteTool(id: number) {
  const success = await deleteTool(id);
  if (success && selectedToolId.value === id) {
    selectedToolId.value = null;
    showEditor.value = false;
  }
}

async function handleSaveTool(toolData: Omit<CustomTool, 'id' | 'created_at' | 'updated_at'>) {
  if (isCreating.value) {
    const created = await createTool(toolData);
    if (created) {
      selectedToolId.value = created.id!;
      isCreating.value = false;
    }
  } else if (selectedToolId.value) {
    await updateTool(selectedToolId.value, toolData);
  }
}

function handleCancelEdit() {
  showEditor.value = false;
  isCreating.value = false;
}
</script>

<template>
  <div class="h-full flex">
    <!-- Left Panel: Tools List -->
    <div class="w-80 border-r theme-border flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b theme-border">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold theme-text">Custom Tools</h2>
          <span class="text-xs theme-text-muted">
            {{ enabledCount }}/{{ toolCount }} active
          </span>
        </div>

        <!-- Create button -->
        <button
          @click="handleCreateNew"
          class="w-full px-4 py-2 bg-buildos-primary hover:bg-buildos-secondary text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>New Tool</span>
        </button>
      </div>

      <!-- Error display -->
      <div v-if="error" class="mx-4 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
        <p class="text-sm text-red-400">{{ error }}</p>
        <button @click="clearError" class="text-xs text-red-300 underline mt-1">Dismiss</button>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading" class="flex-1 flex items-center justify-center">
        <div class="animate-spin w-6 h-6 border-2 border-buildos-primary border-t-transparent rounded-full"></div>
      </div>

      <!-- Tools list -->
      <div v-else class="flex-1 overflow-y-auto p-4">
        <ToolsList
          :tools="tools"
          :selected-id="selectedToolId"
          @select="handleSelectTool"
          @toggle="handleToggleTool"
          @delete="handleDeleteTool"
        />
      </div>

      <!-- Footer info -->
      <div class="p-4 border-t theme-border">
        <p class="text-xs theme-text-muted">
          Tools are available to the orchestrator as <code class="font-mono">mcp__custom__*</code>
        </p>
      </div>
    </div>

    <!-- Right Panel: Editor or Welcome -->
    <div class="flex-1 theme-surface">
      <ToolEditor
        v-if="showEditor"
        :tool="selectedTool"
        :templates="templates"
        :is-new="isCreating"
        @save="handleSaveTool"
        @cancel="handleCancelEdit"
      />

      <!-- Welcome state -->
      <div v-else class="h-full flex items-center justify-center">
        <div class="text-center max-w-md">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-buildos-primary/20 flex items-center justify-center">
            <svg class="w-8 h-8 text-buildos-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium theme-text mb-2">Custom MCP Tools</h3>
          <p class="theme-text-secondary text-sm mb-4">
            Create custom tools that the AI orchestrator can use. Build API integrations, data processors, or any automation you need.
          </p>
          <button
            @click="handleCreateNew"
            class="px-4 py-2 bg-buildos-primary hover:bg-buildos-secondary text-white font-medium rounded-lg transition-colors"
          >
            Create Your First Tool
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
