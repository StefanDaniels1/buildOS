<script setup lang="ts">
import { ref, toRef, onMounted, onUnmounted } from 'vue';
import type { HookEvent } from '../types';
import { useChartData, type TimeRange } from '../composables/useChartData';
import { useEventColors } from '../composables/useEventColors';
import { useEventEmojis } from '../composables/useEventEmojis';

const props = defineProps<{
  events: HookEvent[];
}>();

const eventsRef = toRef(props, 'events');
const { chartData, maxCount, timeRange, setTimeRange, TIME_RANGES } = useChartData(eventsRef);
const { getSessionColor } = useEventColors();
const { getEmoji } = useEventEmojis();

const canvasRef = ref<HTMLCanvasElement | null>(null);
let animationFrame: number | null = null;

const timeRanges: TimeRange[] = ['1m', '2m', '3m', '5m', '10m'];

function draw() {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  // Set canvas size
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 10, right: 10, bottom: 20, left: 10 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Clear
  ctx.fillStyle = '#0f0f1a';
  ctx.fillRect(0, 0, width, height);

  // Draw bars
  const data = chartData.value;
  const barWidth = chartWidth / data.length - 1;
  const max = maxCount.value;

  data.forEach((point, i) => {
    const x = padding.left + i * (barWidth + 1);
    const barHeight = (point.count / max) * chartHeight;
    const y = padding.top + chartHeight - barHeight;

    // Get color based on most frequent session in this bucket
    let color = '#333';
    if (point.count > 0) {
      const sessions = Object.entries(point.sessions);
      if (sessions.length > 0) {
        sessions.sort((a, b) => b[1] - a[1]);
        color = getSessionColor(sessions[0][0]);
      }
    }

    // Draw bar
    ctx.fillStyle = color;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Glow effect for active bars
    if (point.count > 0) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 5;
      ctx.fillRect(x, y, barWidth, barHeight);
      ctx.shadowBlur = 0;
    }
  });

  // Draw event emojis as moving markers (newest at right)
  try {
    const config = TIME_RANGES[timeRange.value];
    const now = Date.now();
    const totalDuration = config.buckets * config.interval;
    const startTime = now - totalDuration;

    // Emoji style
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';

    for (const ev of eventsRef.value) {
      const t = ev.timestamp || 0;
      if (t < startTime || t > now) continue;

      const rel = (t - startTime) / totalDuration; // 0..1
      const ex = padding.left + rel * chartWidth;
      const ey = padding.top + 12; // near top

      // Draw emoji
      ctx.fillText(getEmoji(ev.hook_event_type), ex, ey);
    }
  } catch (e) {
    // ignore if timeRange not initialized yet
  }

  // Draw time labels
  ctx.fillStyle = '#666';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';

  ctx.fillText('now', width - padding.right - 20, height - 5);
  ctx.fillText(`-${timeRange.value}`, padding.left + 20, height - 5);

  animationFrame = requestAnimationFrame(draw);
}

onMounted(() => {
  draw();
});

onUnmounted(() => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame);
  }
});
</script>

<template>
  <div class="card p-3">
    <!-- Time range selector -->
    <div class="flex justify-between items-center mb-2">
      <span class="text-sm text-gray-400">Event Activity</span>
      <div class="flex gap-1">
        <button
          v-for="range in timeRanges"
          :key="range"
          @click="setTimeRange(range)"
          class="px-2 py-1 text-xs rounded transition-colors"
          :class="timeRange === range
            ? 'bg-buildos-primary text-white'
            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'"
        >
          {{ range }}
        </button>
      </div>
    </div>

    <!-- Chart canvas -->
    <canvas
      ref="canvasRef"
      class="w-full h-32 rounded"
    />

    <!-- Stats -->
    <div class="flex justify-between mt-2 text-xs text-gray-500">
      <span>{{ events.length }} total events</span>
      <span>Peak: {{ maxCount }} / bucket</span>
    </div>
  </div>
</template>
