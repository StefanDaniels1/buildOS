<script setup lang="ts">
import { computed, ref } from 'vue';
import type { HookEvent } from '../types';
import { useEventColors } from '../composables/useEventColors';
import { useEventEmojis } from '../composables/useEventEmojis';

const props = defineProps<{
  event: HookEvent;
}>();

const { getSessionColor, getEventTypeColor } = useEventColors();
const { getEmoji } = useEventEmojis();

const expanded = ref(false);

const sessionColor = computed(() => getSessionColor(props.event.session_id));
const eventColor = computed(() => getEventTypeColor(props.event.hook_event_type));
const emoji = computed(() => getEmoji(props.event.hook_event_type));

const eventSummary = computed(() => {
  const payload = props.event.payload;
  const type = props.event.hook_event_type;

  switch (type) {
    case 'UserPromptSubmit':
      return payload.prompt ? `"${String(payload.prompt).slice(0, 50)}..."` : '';
    case 'AgentThinking':
      return payload.thought ? String(payload.thought).slice(0, 80) : '';
    case 'SubagentStart':
      return `${payload.agent_type || 'agent'}: ${payload.description || ''}`;
    case 'ToolStart':
    case 'ToolStop':
    case 'PreToolUse':
    case 'PostToolUse':
      return payload.tool_name || '';
    case 'Stop':
      return payload.status === 'error' ? `Error: ${payload.message}` : payload.message;
    case 'AgentMetrics':
      return `Cost: $${payload.cost_usd || 0} | Turns: ${payload.num_turns || 0}`;
    default:
      return props.event.summary || '';
  }
});

function formatTime(timestamp?: number): string {
  if (!timestamp) return '';
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}
</script>

<template>
  <div
    class="rounded-md border border-gray-700 bg-buildos-dark hover:border-gray-600 transition-colors cursor-pointer"
    @click="expanded = !expanded"
  >
    <!-- Compact view -->
    <div class="flex items-center gap-2 p-2">
      <!-- Session indicator -->
      <div
        class="w-1 h-8 rounded-full flex-shrink-0"
        :style="{ backgroundColor: sessionColor }"
      />

      <!-- Emoji -->
      <span class="text-lg">{{ emoji }}</span>

      <!-- Event type -->
      <span
        class="text-xs font-medium px-2 py-0.5 rounded"
        :style="{ backgroundColor: eventColor + '30', color: eventColor }"
      >
        {{ event.hook_event_type }}
      </span>

      <!-- Summary -->
      <span class="flex-1 text-sm text-gray-300 truncate">
        {{ eventSummary }}
      </span>

      <!-- Timestamp -->
      <span class="text-xs text-gray-500 flex-shrink-0">
        {{ formatTime(event.timestamp) }}
      </span>

      <!-- Expand indicator -->
      <svg
        class="w-4 h-4 text-gray-500 transition-transform"
        :class="{ 'rotate-180': expanded }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>

    <!-- Expanded view -->
    <div v-if="expanded" class="border-t border-gray-700 p-3">
      <div class="text-xs space-y-2">
        <div class="flex gap-2">
          <span class="text-gray-500">Session:</span>
          <span class="font-mono" :style="{ color: sessionColor }">
            {{ event.session_id.slice(0, 8) }}...
          </span>
        </div>
        <div class="flex gap-2">
          <span class="text-gray-500">Source:</span>
          <span>{{ event.source_app }}</span>
        </div>
        <div class="mt-2">
          <span class="text-gray-500">Payload:</span>
          <pre class="mt-1 p-2 bg-buildos-darker rounded text-xs overflow-x-auto">{{ JSON.stringify(event.payload, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
