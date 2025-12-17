<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import type { HookEvent } from '../types';
import { useTheme } from '../composables/useTheme';

const props = defineProps<{
  events: HookEvent[];
}>();

const emit = defineEmits<{
  (e: 'nodeClick', eventId: string): void;
}>();

const { theme } = useTheme();

// Canvas and container refs
const canvasRef = ref<HTMLCanvasElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);

// Pan and zoom state
const scale = ref(1);
const panX = ref(0);
const panY = ref(0);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const lastPan = ref({ x: 0, y: 0 });

// Hover state
const hoveredNode = ref<string | null>(null);
const tooltipPos = ref({ x: 0, y: 0 });
const tooltipEvent = ref<HookEvent | null>(null);

// Node types and their visual properties
const nodeConfig = {
  SessionStart: { emoji: '🚀', color: '#22c55e', label: 'Start' },
  UserPromptSubmit: { emoji: '💬', color: '#3b82f6', label: 'User' },
  AgentThinking: { emoji: '🧠', color: '#8b5cf6', label: 'Think' },
  SubagentStart: { emoji: '🔀', color: '#f59e0b', label: 'Fork' },
  SubagentEnd: { emoji: '✅', color: '#10b981', label: 'Join' },
  AgentMetrics: { emoji: '📊', color: '#06b6d4', label: 'Metrics' },
  Stop: { emoji: '🏁', color: '#ef4444', label: 'Stop' },
  SessionEnd: { emoji: '🔚', color: '#6b7280', label: 'End' },
  default: { emoji: '📌', color: '#9ca3af', label: 'Event' }
};

// Layout constants
const NODE_SPACING = 100;
const LANE_HEIGHT = 70;
const START_X = 80;
const BASE_Y = 50;
const NODE_RADIUS = 16;

// Build the flow tree structure from events
interface FlowNode {
  id: string;
  event: HookEvent;
  x: number;
  y: number;
  lane: number;
  agentId: string;
  type: string;
}

interface FlowConnection {
  from: FlowNode;
  to: FlowNode;
  type: 'main' | 'spawn' | 'return';
}

const flowData = computed(() => {
  const nodes: FlowNode[] = [];
  const connections: FlowConnection[] = [];

  const agentLanes: Map<string, number> = new Map();
  agentLanes.set('orchestrator', 0);
  let nextLane = 1;

  const sortedEvents = [...props.events].sort((a, b) =>
    (a.timestamp || 0) - (b.timestamp || 0)
  );

  if (sortedEvents.length === 0) return { nodes, connections, width: 400, height: 200, maxLane: 0 };

  let currentX = START_X;
  const prevNodeByLane: Map<number, FlowNode> = new Map();
  const subagentSpawns: Map<string, FlowNode> = new Map();
  const activeAgents: Set<string> = new Set();
  let maxLane = 0;

  // Track orchestrator nodes for return connections
  const orchestratorNodes: FlowNode[] = [];

  for (const event of sortedEvents) {
    const type = event.hook_event_type;
    let lane = 0;
    let agentId = 'orchestrator';

    if (type === 'SubagentStart') {
      agentId = event.payload.agent_id as string || `subagent_${nextLane}`;
      if (!agentLanes.has(agentId)) {
        agentLanes.set(agentId, nextLane++);
      }
      lane = agentLanes.get(agentId) || 0;
      activeAgents.add(agentId);
      maxLane = Math.max(maxLane, lane);
    } else if (type === 'SubagentEnd') {
      agentId = event.payload.agent_id as string || 'unknown';
      lane = agentLanes.get(agentId) || 0;
      activeAgents.delete(agentId);
    } else if (event.payload?.agent_id && typeof event.payload.agent_id === 'string' && agentLanes.has(event.payload.agent_id)) {
      agentId = event.payload.agent_id as string;
      lane = agentLanes.get(agentId) ?? 0;
    } else {
      lane = 0;
      agentId = 'orchestrator';
    }

    const node: FlowNode = {
      id: event.id,
      event,
      x: currentX,
      y: BASE_Y + lane * LANE_HEIGHT,
      lane,
      agentId,
      type
    };

    nodes.push(node);

    if (lane === 0) {
      orchestratorNodes.push(node);
    }

    if (type === 'SubagentStart') {
      subagentSpawns.set(agentId, node);

      // Connect from last orchestrator node to spawn
      if (orchestratorNodes.length > 0) {
        const lastOrch = orchestratorNodes[orchestratorNodes.length - 1];
        if (lastOrch.id !== node.id) {
          connections.push({
            from: lastOrch,
            to: node,
            type: 'spawn'
          });
        }
      }
    } else if (type === 'SubagentEnd') {
      // Connect from spawn to end
      const spawnNode = subagentSpawns.get(agentId);
      if (spawnNode) {
        connections.push({
          from: spawnNode,
          to: node,
          type: 'main'
        });
      }

      // Connect return to NEXT orchestrator node (will be created later)
      // Store for post-processing
    } else {
      const prevNode = prevNodeByLane.get(lane);
      if (prevNode && prevNode.type !== 'SubagentStart') {
        connections.push({
          from: prevNode,
          to: node,
          type: 'main'
        });
      }
    }

    prevNodeByLane.set(lane, node);
    currentX += NODE_SPACING;
  }

  // Post-process: Add return connections from SubagentEnd to next orchestrator node
  for (const node of nodes) {
    if (node.type === 'SubagentEnd') {
      // Find next orchestrator node after this one
      const nextOrchNode = orchestratorNodes.find(n => n.x > node.x);
      if (nextOrchNode) {
        connections.push({
          from: node,
          to: nextOrchNode,
          type: 'return'
        });
      }
    }
  }

  const totalWidth = Math.max(currentX + 100, 400);
  const totalHeight = Math.max((maxLane + 1) * LANE_HEIGHT + BASE_Y + 50, 200);

  return { nodes, connections, width: totalWidth, height: totalHeight, maxLane };
});

// Theme colors
const bgColor = computed(() => theme.value === 'dark' ? '#0a0a14' : '#f8fafc');
const gridColor = computed(() => theme.value === 'dark' ? '#1a1a2e' : '#e2e8f0');
const textColor = computed(() => theme.value === 'dark' ? '#9ca3af' : '#6b7280');
const orchLineColor = computed(() => theme.value === 'dark' ? '#22c55e' : '#16a34a');

function getNodeConfig(type: string) {
  return nodeConfig[type as keyof typeof nodeConfig] || nodeConfig.default;
}

function draw() {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const { nodes, connections, width, height, maxLane } = flowData.value;

  // Set canvas size
  const canvasWidth = Math.max(width, 800);
  const canvasHeight = Math.max(height, 300);

  canvas.width = canvasWidth * dpr;
  canvas.height = canvasHeight * dpr;
  canvas.style.width = `${canvasWidth}px`;
  canvas.style.height = `${canvasHeight}px`;

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Apply pan and zoom
  ctx.save();
  ctx.translate(panX.value, panY.value);
  ctx.scale(scale.value, scale.value);

  // Clear with background
  ctx.fillStyle = bgColor.value;
  ctx.fillRect(-panX.value / scale.value, -panY.value / scale.value, canvasWidth / scale.value + 100, canvasHeight / scale.value + 100);

  // Draw grid
  ctx.strokeStyle = gridColor.value;
  ctx.lineWidth = 1;
  for (let x = 0; x < width + 200; x += 50) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height + 100);
    ctx.stroke();
  }
  for (let y = 0; y < height + 100; y += 50) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width + 200, y);
    ctx.stroke();
  }

  // Draw lane backgrounds
  for (let lane = 0; lane <= maxLane; lane++) {
    const y = BASE_Y + lane * LANE_HEIGHT - LANE_HEIGHT / 2 + 10;
    ctx.fillStyle = lane === 0
      ? (theme.value === 'dark' ? 'rgba(34, 197, 94, 0.05)' : 'rgba(34, 197, 94, 0.08)')
      : (theme.value === 'dark' ? 'rgba(245, 158, 11, 0.05)' : 'rgba(245, 158, 11, 0.08)');
    ctx.fillRect(0, y, width + 100, LANE_HEIGHT - 10);
  }

  // Draw lane labels (fixed position)
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';

  for (let lane = 0; lane <= maxLane; lane++) {
    const y = BASE_Y + lane * LANE_HEIGHT;
    ctx.fillStyle = lane === 0 ? '#22c55e' : '#f59e0b';
    const label = lane === 0 ? '🤖 Orchestrator' : `🔀 Agent ${lane}`;
    ctx.fillText(label, 8, y);
  }

  // Draw orchestrator main line
  const lane0Nodes = nodes.filter(n => n.lane === 0);
  if (lane0Nodes.length > 1) {
    ctx.strokeStyle = orchLineColor.value;
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.setLineDash([]);

    ctx.beginPath();
    ctx.moveTo(lane0Nodes[0].x, lane0Nodes[0].y);
    for (let i = 1; i < lane0Nodes.length; i++) {
      ctx.lineTo(lane0Nodes[i].x, lane0Nodes[i].y);
    }
    ctx.stroke();
  }

  // Draw connections
  for (const conn of connections) {
    if (conn.type === 'spawn') {
      // Fork: curved line from orchestrator down to subagent
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);

      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);

      const midX = conn.from.x + (conn.to.x - conn.from.x) * 0.3;
      ctx.bezierCurveTo(
        midX, conn.from.y,
        midX, conn.to.y,
        conn.to.x, conn.to.y
      );
      ctx.stroke();

      // Draw arrow
      ctx.setLineDash([]);
      const angle = Math.atan2(conn.to.y - conn.from.y, conn.to.x - conn.from.x);
      ctx.beginPath();
      ctx.moveTo(conn.to.x - NODE_RADIUS - 5, conn.to.y);
      ctx.lineTo(conn.to.x - NODE_RADIUS - 15, conn.to.y - 6);
      ctx.lineTo(conn.to.x - NODE_RADIUS - 15, conn.to.y + 6);
      ctx.closePath();
      ctx.fillStyle = '#f59e0b';
      ctx.fill();

    } else if (conn.type === 'return') {
      // Return: curved line from subagent back up to orchestrator
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);

      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);

      const midX = conn.from.x + (conn.to.x - conn.from.x) * 0.7;
      ctx.bezierCurveTo(
        midX, conn.from.y,
        midX, conn.to.y,
        conn.to.x, conn.to.y
      );
      ctx.stroke();

      // Draw arrow
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(conn.to.x - NODE_RADIUS - 5, conn.to.y);
      ctx.lineTo(conn.to.x - NODE_RADIUS - 15, conn.to.y - 6);
      ctx.lineTo(conn.to.x - NODE_RADIUS - 15, conn.to.y + 6);
      ctx.closePath();
      ctx.fillStyle = '#10b981';
      ctx.fill();

    } else if (conn.from.lane > 0) {
      // Subagent lane line
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 3;
      ctx.setLineDash([]);
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);
      ctx.lineTo(conn.to.x, conn.to.y);
      ctx.stroke();
    }
  }
  ctx.setLineDash([]);

  // Draw nodes
  for (const node of nodes) {
    const config = getNodeConfig(node.type);
    const isHovered = hoveredNode.value === node.id;
    const radius = isHovered ? NODE_RADIUS + 4 : NODE_RADIUS;

    // Glow effect
    if (isHovered) {
      ctx.shadowColor = config.color;
      ctx.shadowBlur = 20;
    }

    // Node circle with gradient
    const gradient = ctx.createRadialGradient(node.x - 3, node.y - 3, 0, node.x, node.y, radius);
    gradient.addColorStop(0, config.color);
    gradient.addColorStop(1, adjustColor(config.color, -30));

    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Border
    ctx.strokeStyle = theme.value === 'dark' ? '#fff' : '#1f2937';
    ctx.lineWidth = isHovered ? 3 : 2;
    ctx.stroke();

    ctx.shadowBlur = 0;

    // Emoji
    ctx.font = `${isHovered ? 16 : 14}px system-ui, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#fff';
    ctx.fillText(config.emoji, node.x, node.y + 1);
  }

  ctx.restore();
}

function adjustColor(color: string, amount: number): string {
  const hex = color.replace('#', '');
  const r = Math.max(0, Math.min(255, parseInt(hex.substr(0, 2), 16) + amount));
  const g = Math.max(0, Math.min(255, parseInt(hex.substr(2, 2), 16) + amount));
  const b = Math.max(0, Math.min(255, parseInt(hex.substr(4, 2), 16) + amount));
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

// Transform screen coords to canvas coords
function screenToCanvas(screenX: number, screenY: number) {
  const canvas = canvasRef.value;
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();
  const x = (screenX - rect.left - panX.value) / scale.value;
  const y = (screenY - rect.top - panY.value) / scale.value;
  return { x, y };
}

// Mouse handlers
function handleMouseMove(e: MouseEvent) {
  if (isDragging.value) {
    panX.value = lastPan.value.x + (e.clientX - dragStart.value.x);
    panY.value = lastPan.value.y + (e.clientY - dragStart.value.y);
    draw();
    return;
  }

  const { x, y } = screenToCanvas(e.clientX, e.clientY);

  let found = false;
  for (const node of flowData.value.nodes) {
    const dx = x - node.x;
    const dy = y - node.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < NODE_RADIUS + 5) {
      hoveredNode.value = node.id;
      tooltipEvent.value = node.event;
      tooltipPos.value = { x: e.clientX, y: e.clientY };
      found = true;
      break;
    }
  }

  if (!found) {
    hoveredNode.value = null;
    tooltipEvent.value = null;
  }
}

function handleMouseDown(e: MouseEvent) {
  const { x, y } = screenToCanvas(e.clientX, e.clientY);

  // Check for node click
  for (const node of flowData.value.nodes) {
    const dx = x - node.x;
    const dy = y - node.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < NODE_RADIUS + 5) {
      emit('nodeClick', node.id);
      return;
    }
  }

  // Start drag
  isDragging.value = true;
  dragStart.value = { x: e.clientX, y: e.clientY };
  lastPan.value = { x: panX.value, y: panY.value };
}

function handleMouseUp() {
  isDragging.value = false;
}

function handleMouseLeave() {
  isDragging.value = false;
  hoveredNode.value = null;
  tooltipEvent.value = null;
}

function handleWheel(e: WheelEvent) {
  e.preventDefault();

  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.3, Math.min(2, scale.value * delta));

  // Zoom toward mouse position
  const canvas = canvasRef.value;
  if (canvas) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    panX.value = mouseX - (mouseX - panX.value) * (newScale / scale.value);
    panY.value = mouseY - (mouseY - panY.value) * (newScale / scale.value);
  }

  scale.value = newScale;
  draw();
}

// Zoom controls
function zoomIn() {
  scale.value = Math.min(2, scale.value * 1.2);
  draw();
}

function zoomOut() {
  scale.value = Math.max(0.3, scale.value / 1.2);
  draw();
}

function resetView() {
  scale.value = 1;
  panX.value = 0;
  panY.value = 0;
  draw();
}

function fitToView() {
  const container = containerRef.value;
  const { width, height } = flowData.value;
  if (!container || width === 0) return;

  const containerWidth = container.clientWidth - 20;
  const containerHeight = container.clientHeight - 20;

  const scaleX = containerWidth / width;
  const scaleY = containerHeight / height;
  scale.value = Math.min(scaleX, scaleY, 1);
  panX.value = 10;
  panY.value = 10;
  draw();
}

// Watch for changes
watch([flowData, theme, hoveredNode, scale, panX, panY], () => {
  draw();
}, { deep: true });

onMounted(() => {
  nextTick(() => {
    draw();
    // Auto fit on mount
    setTimeout(fitToView, 100);
  });
});

function formatTime(ts: number | undefined): string {
  if (!ts) return 'N/A';
  return new Date(ts).toLocaleTimeString();
}

function getShortMessage(event: HookEvent): string {
  const payload = event.payload;
  if (payload.prompt) return String(payload.prompt).slice(0, 60) + '...';
  if (payload.thought) return String(payload.thought).slice(0, 60) + '...';
  if (payload.description) return String(payload.description).slice(0, 60) + '...';
  if (payload.message) return String(payload.message).slice(0, 60) + '...';
  if (payload.agent_type) return `Agent: ${payload.agent_type}`;
  return event.hook_event_type;
}
</script>

<template>
  <div class="card p-3">
    <!-- Header with controls -->
    <div class="flex justify-between items-center mb-2">
      <span class="text-sm font-medium theme-text-secondary">🌳 Agent Flow</span>
      <div class="flex items-center gap-2">
        <span class="text-xs theme-text-muted">{{ flowData.nodes.length }} events</span>
        <span class="text-xs theme-text-muted">•</span>
        <span class="text-xs theme-text-muted">{{ Math.round(scale * 100) }}%</span>

        <!-- Zoom controls -->
        <div class="flex items-center gap-1 ml-2">
          <button
            @click="zoomOut"
            class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-xs"
            title="Zoom out"
          >
            ➖
          </button>
          <button
            @click="zoomIn"
            class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-xs"
            title="Zoom in"
          >
            ➕
          </button>
          <button
            @click="fitToView"
            class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-xs"
            title="Fit to view"
          >
            ⛶
          </button>
          <button
            @click="resetView"
            class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-xs"
            title="Reset view"
          >
            ↺
          </button>
        </div>
      </div>
    </div>

    <!-- Flow visualization container -->
    <div
      ref="containerRef"
      class="relative rounded border overflow-hidden"
      :class="[
        isDragging ? 'cursor-grabbing' : 'cursor-grab',
        theme === 'dark' ? 'border-gray-700 bg-[#0a0a14]' : 'border-gray-200 bg-slate-50'
      ]"
      style="height: 280px;"
      @mousemove="handleMouseMove"
      @mousedown="handleMouseDown"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      @wheel="handleWheel"
    >
      <canvas
        ref="canvasRef"
        class="block"
      />

      <!-- Empty state -->
      <div
        v-if="flowData.nodes.length === 0"
        class="absolute inset-0 flex items-center justify-center theme-text-muted"
      >
        <div class="text-center">
          <div class="text-3xl mb-2">🌱</div>
          <div class="text-sm font-medium">No events yet</div>
          <div class="text-xs opacity-70">Send a message to see the agent flow</div>
        </div>
      </div>

      <!-- Pan/zoom hint -->
      <div
        v-if="flowData.nodes.length > 0"
        class="absolute bottom-2 right-2 text-xs theme-text-muted opacity-60"
      >
        Scroll to zoom • Drag to pan
      </div>
    </div>

    <!-- Tooltip -->
    <Teleport to="body">
      <div
        v-if="tooltipEvent"
        class="fixed z-50 px-3 py-2 rounded-lg shadow-xl text-sm max-w-sm pointer-events-none border"
        :class="theme === 'dark' ? 'bg-gray-800 text-white border-gray-600' : 'bg-white text-gray-900 border-gray-200'"
        :style="{
          left: `${tooltipPos.x + 15}px`,
          top: `${tooltipPos.y - 10}px`
        }"
      >
        <div class="font-semibold flex items-center gap-2 mb-1">
          <span class="text-lg">{{ getNodeConfig(tooltipEvent.hook_event_type).emoji }}</span>
          <span>{{ tooltipEvent.hook_event_type }}</span>
        </div>
        <div class="text-xs opacity-60 mb-1">{{ formatTime(tooltipEvent.timestamp) }}</div>
        <div class="text-xs leading-relaxed">{{ getShortMessage(tooltipEvent) }}</div>
        <div class="text-xs mt-2 text-blue-400 font-medium">Click to view details</div>
      </div>
    </Teleport>

    <!-- Legend -->
    <div class="flex flex-wrap gap-4 mt-3 text-xs">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full bg-green-500"></span>
        <span class="theme-text-muted">Orchestrator</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full bg-amber-500"></span>
        <span class="theme-text-muted">Subagent</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="inline-block w-5 border-t-2 border-dashed border-amber-500"></span>
        <span class="theme-text-muted">Fork</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="inline-block w-5 border-t-2 border-dashed border-emerald-500"></span>
        <span class="theme-text-muted">Join</span>
      </div>
    </div>
  </div>
</template>
