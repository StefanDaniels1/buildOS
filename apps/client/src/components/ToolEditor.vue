<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { CustomTool, ToolTemplate } from '../composables/useTools';

const props = defineProps<{
  tool: CustomTool | null;
  templates: ToolTemplate[];
  isNew: boolean;
}>();

const emit = defineEmits<{
  (e: 'save', tool: Omit<CustomTool, 'id' | 'created_at' | 'updated_at'>): void;
  (e: 'cancel'): void;
}>();

// Form state
const name = ref('');
const description = ref('');
const inputSchemaJson = ref('{}');
const handlerCode = ref('');
const enabled = ref(true);
const envVarsJson = ref('{}');

// Validation
const nameError = ref('');
const schemaError = ref('');
const codeError = ref('');
const envVarsError = ref('');

// Reset form when tool changes
watch(() => props.tool, (newTool) => {
  if (newTool) {
    name.value = newTool.name;
    description.value = newTool.description;
    inputSchemaJson.value = JSON.stringify(newTool.input_schema, null, 2);
    handlerCode.value = newTool.handler_code;
    enabled.value = newTool.enabled;
    envVarsJson.value = JSON.stringify(newTool.env_vars || {}, null, 2);
  } else {
    resetForm();
  }
  clearErrors();
}, { immediate: true });

function resetForm() {
  name.value = '';
  description.value = '';
  inputSchemaJson.value = '{}';
  handlerCode.value = `async def tool_name(args: dict) -> dict:
    """
    Tool description here.

    Args:
        args: Dictionary of input parameters

    Returns:
        Dictionary with success status and data
    """
    # Your code here
    return {"success": True, "data": {}}`;
  enabled.value = true;
  envVarsJson.value = '{}';
}

function clearErrors() {
  nameError.value = '';
  schemaError.value = '';
  codeError.value = '';
  envVarsError.value = '';
}

function loadTemplate(template: ToolTemplate) {
  name.value = template.name;
  description.value = template.description;
  inputSchemaJson.value = JSON.stringify(template.input_schema, null, 2);
  handlerCode.value = template.handler_code;
  envVarsJson.value = JSON.stringify(template.env_vars || {}, null, 2);
  clearErrors();
}

function validate(): boolean {
  clearErrors();
  let isValid = true;

  // Validate name
  if (!name.value.trim()) {
    nameError.value = 'Name is required';
    isValid = false;
  } else if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name.value)) {
    nameError.value = 'Name must start with letter/underscore, contain only letters, numbers, underscores';
    isValid = false;
  }

  // Validate input schema JSON
  try {
    JSON.parse(inputSchemaJson.value);
  } catch {
    schemaError.value = 'Invalid JSON';
    isValid = false;
  }

  // Validate handler code
  if (!handlerCode.value.trim()) {
    codeError.value = 'Handler code is required';
    isValid = false;
  } else if (!handlerCode.value.includes('async def')) {
    codeError.value = 'Handler must be an async function (async def)';
    isValid = false;
  }

  // Validate env vars JSON
  try {
    JSON.parse(envVarsJson.value);
  } catch {
    envVarsError.value = 'Invalid JSON';
    isValid = false;
  }

  return isValid;
}

function handleSave() {
  if (!validate()) return;

  const tool = {
    name: name.value.trim(),
    description: description.value.trim(),
    input_schema: JSON.parse(inputSchemaJson.value),
    handler_code: handlerCode.value,
    enabled: enabled.value,
    env_vars: JSON.parse(envVarsJson.value)
  };

  emit('save', tool);
}

const title = computed(() => props.isNew ? 'Create New Tool' : `Edit: ${props.tool?.name}`);
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="p-4 border-b theme-border flex items-center justify-between">
      <h3 class="font-medium theme-text">{{ title }}</h3>
      <button
        @click="emit('cancel')"
        class="theme-text-muted hover:theme-text transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Form -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Templates dropdown (only for new tools) -->
      <div v-if="isNew && templates.length > 0">
        <label class="block text-sm font-medium theme-text-secondary mb-1">Load Template</label>
        <select
          class="input-field w-full"
          @change="(e) => {
            const t = templates.find(t => t.name === (e.target as HTMLSelectElement).value);
            if (t) loadTemplate(t);
          }"
        >
          <option value="">Select a template...</option>
          <option v-for="t in templates" :key="t.name" :value="t.name">
            {{ t.name }} - {{ t.description.slice(0, 50) }}...
          </option>
        </select>
      </div>

      <!-- Name -->
      <div>
        <label class="block text-sm font-medium theme-text-secondary mb-1">
          Tool Name <span class="text-red-400">*</span>
        </label>
        <input
          v-model="name"
          type="text"
          placeholder="my_tool_name"
          class="input-field w-full font-mono"
          :class="{ 'border-red-500': nameError }"
        />
        <p v-if="nameError" class="text-xs text-red-400 mt-1">{{ nameError }}</p>
        <p class="text-xs theme-text-muted mt-1">Used as: mcp__custom__{{ name || 'tool_name' }}</p>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium theme-text-secondary mb-1">
          Description <span class="text-red-400">*</span>
        </label>
        <textarea
          v-model="description"
          rows="2"
          placeholder="What does this tool do? This helps Claude understand when to use it."
          class="input-field w-full resize-none"
        ></textarea>
      </div>

      <!-- Input Schema -->
      <div>
        <label class="block text-sm font-medium theme-text-secondary mb-1">
          Input Parameters (JSON)
        </label>
        <textarea
          v-model="inputSchemaJson"
          rows="4"
          placeholder='{"param_name": "str", "count": "int"}'
          class="input-field w-full font-mono text-sm resize-none"
          :class="{ 'border-red-500': schemaError }"
        ></textarea>
        <p v-if="schemaError" class="text-xs text-red-400 mt-1">{{ schemaError }}</p>
        <p class="text-xs theme-text-muted mt-1">Types: str, int, float, bool, list, dict</p>
      </div>

      <!-- Handler Code -->
      <div>
        <label class="block text-sm font-medium theme-text-secondary mb-1">
          Python Handler Code <span class="text-red-400">*</span>
        </label>
        <textarea
          v-model="handlerCode"
          rows="15"
          placeholder="async def tool_name(args: dict) -> dict:"
          class="input-field w-full font-mono text-sm resize-none"
          :class="{ 'border-red-500': codeError }"
          style="tab-size: 4;"
        ></textarea>
        <p v-if="codeError" class="text-xs text-red-400 mt-1">{{ codeError }}</p>
        <p class="text-xs theme-text-muted mt-1">Function name must match tool name. Use httpx for HTTP requests.</p>
      </div>

      <!-- Environment Variables -->
      <div>
        <label class="block text-sm font-medium theme-text-secondary mb-1">
          Environment Variables (JSON)
        </label>
        <textarea
          v-model="envVarsJson"
          rows="3"
          placeholder='{"API_KEY": "your_key_here"}'
          class="input-field w-full font-mono text-sm resize-none"
          :class="{ 'border-red-500': envVarsError }"
        ></textarea>
        <p v-if="envVarsError" class="text-xs text-red-400 mt-1">{{ envVarsError }}</p>
        <p class="text-xs theme-text-muted mt-1">Access via os.environ.get("KEY")</p>
      </div>

      <!-- Enabled toggle -->
      <div class="flex items-center gap-3">
        <button
          @click="enabled = !enabled"
          class="relative w-10 h-5 rounded-full transition-colors"
          :class="enabled ? 'bg-green-500' : 'bg-gray-600'"
        >
          <span
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
            :class="enabled ? 'left-5' : 'left-0.5'"
          ></span>
        </button>
        <span class="text-sm theme-text">{{ enabled ? 'Enabled' : 'Disabled' }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="p-4 border-t theme-border flex gap-3">
      <button
        @click="handleSave"
        class="flex-1 px-4 py-2 bg-buildos-primary hover:bg-buildos-secondary text-white font-medium rounded-lg transition-colors"
      >
        {{ isNew ? 'Create Tool' : 'Save Changes' }}
      </button>
      <button
        @click="emit('cancel')"
        class="px-4 py-2 theme-surface theme-border border hover:opacity-80 theme-text font-medium rounded-lg transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
</template>
