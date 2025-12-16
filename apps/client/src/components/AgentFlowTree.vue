<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
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

// Drag/pan state
const isDragging = ref(false);
const dragStartX = ref(0);
const scrollOffset = ref(0);
const containerWidth = ref(800);

// Hover state
const hoveredNode = ref<string | null>(null);
const tooltipPos = ref({ x: 0, y: 0 });
const tooltipEvent = ref<HookEvent | null>(null);

// Node types and their visual properties
const nodeConfig = {
  SessionStart: { emoji: '🚀', color: '#22c55e', label: 'Start' },
  UserPromptSubmit: { emoji: '💬', color: '#3b82f6', label: 'User' },
  AgentThinking: { emoji: '🧠', color: '#8b5cf6', label: 'Think' },
  SubagentStart: { emoji: '👥', color: '#f59e0b', label: 'Spawn' },
  SubagentEnd: { emoji: '✅', color: '#10b981', label: 'Return' },
  AgentMetrics: { emoji: '📊', color: '#06b6d4', label: 'Metrics' },
  Stop: { emoji: '🏁', color: '#ef4444', label: 'Stop' },
  SessionEnd: { emoji: '🔚', color: '#6b7280', label: 'End' },
  default: { emoji: '📌', color: '#9ca3af', label: 'Event' }
};

// Build the flow tree structure from events
interface FlowNode {
  id: string;
  event: HookEvent;
  x: number;
  y: number;
  lane: number; // 0 = orchestrator, 1+ = subagents
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
  
  // Track active agents and their lanes
  const agentLanes: Map<string, number> = new Map();
  agentLanes.set('orchestrator', 0);
  let nextLane = 1;
  
  // Sort events by timestamp
  const sortedEvents = [...props.events].sort((a, b) => 
    (a.timestamp || 0) - (b.timestamp || 0)
  );
  
  if (sortedEvents.length === 0) return { nodes, connections, width: 400 };
  
  // Layout constants
  const nodeSpacing = 80;
  const laneHeight = 50;
  const startX = 60;
  const baseY = 60;
  
  let currentX = startX;
  let prevNodeByLane: Map<number, FlowNode> = new Map();
  
  // Track subagent spawns to connect returns
  const subagentSpawns: Map<string, FlowNode> = new Map();
  
  for (const event of sortedEvents) {
    const type = event.hook_event_type;
    let lane = 0;
    let agentId = 'orchestrator';
    
    // Determine which lane this event belongs to
    if (type === 'SubagentStart') {
      // New subagent spawned - assign a new lane
      agentId = event.payload.agent_id || `subagent_${nextLane}`;
      if (!agentLanes.has(agentId)) {
        agentLanes.set(agentId, nextLane++);
      }
      lane = agentLanes.get(agentId) || 0;
    } else if (type === 'SubagentEnd') {
      // Subagent completed - find its lane
      agentId = event.payload.agent_id || 'unknown';
      lane = agentLanes.get(agentId) || 0;
    } else if (event.payload?.agent_id && typeof event.payload.agent_id === 'string' && agentLanes.has(event.payload.agent_id)) {
      // Event has agent_id that matches a known subagent - use its lane
      agentId = event.payload.agent_id as string;
      lane = agentLanes.get(agentId) ?? 0;
    } else {
      // Orchestrator event (no agent_id or unknown agent)
      lane = 0;
      agentId = 'orchestrator';
    }
    
    const node: FlowNode = {
      id: event.id,
      event,
      x: currentX,
      y: baseY + lane * laneHeight,
      lane,
      agentId,
      type
    };
    
    nodes.push(node);
    
    // Track subagent spawn for later connection
    if (type === 'SubagentStart') {
      subagentSpawns.set(agentId, node);
    }
    
    // Create connections
    if (type === 'SubagentStart') {
      // Connect from orchestrator main line to subagent spawn
      const prevOrchNode = prevNodeByLane.get(0);
      if (prevOrchNode) {
        connections.push({
          from: prevOrchNode,
          to: node,
          type: 'spawn'
        });
      }
    } else if (type === 'SubagentEnd') {
      // Connect from spawn to end within subagent lane
      const spawnNode = subagentSpawns.get(agentId);
      if (spawnNode) {
        connections.push({
          from: spawnNode,
          to: node,
          type: 'main'
        });
      }
      // Connect back to orchestrator
      const nextOrchNode = prevNodeByLane.get(0);
      if (nextOrchNode) {
        connections.push({
          from: node,
          to: nextOrchNode,
          type: 'return'
        });
      }
    } else {
      // Main line connection
      const prevNode = prevNodeByLane.get(lane);
      if (prevNode) {
        connections.push({
          from: prevNode,
          to: node,
          type: 'main'
        });
      }
    }
    
    prevNodeByLane.set(lane, node);
    currentX += nodeSpacing;
  }
  
  const totalWidth = Math.max(currentX + 60, 400);
  
  return { nodes, connections, width: totalWidth };
});

// Theme-aware colors
const bgColor = computed(() => theme.value === 'dark' ? '#0f0f1a' : '#f8fafc');
const lineColor = computed(() => theme.value === 'dark' ? '#374151' : '#d1d5db');
const textColor = computed(() => theme.value === 'dark' ? '#9ca3af' : '#6b7280');
const orchLineColor = computed(() => theme.value === 'dark' ? '#22c55e' : '#16a34a');

function getNodeConfig(type: string) {
  return nodeConfig[type as keyof typeof nodeConfig] || nodeConfig.default;
}

function draw() {
  const canvas = canvasRef.value;
  const container = containerRef.value;
  if (!canvas || !container) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  const dpr = window.devicePixelRatio || 1;
  const { nodes, connections, width } = flowData.value;
  
  // Set canvas size to full flow width
  const height = 200;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.scale(dpr, dpr);
  
  // Clear
  ctx.fillStyle = bgColor.value;
  ctx.fillRect(0, 0, width, height);
  
  // Draw orchestrator main line (lane 0)
  ctx.strokeStyle = orchLineColor.value;
  ctx.lineWidth = 3;
  ctx.setLineDash([]);
  
  const lane0Nodes = nodes.filter(n => n.lane === 0);
  if (lane0Nodes.length > 1) {
    ctx.beginPath();
    ctx.moveTo(lane0Nodes[0].x, lane0Nodes[0].y);
    for (let i = 1; i < lane0Nodes.length; i++) {
      ctx.lineTo(lane0Nodes[i].x, lane0Nodes[i].y);
    }
    ctx.stroke();
  }
  
  // Draw connections
  for (const conn of connections) {
    const config = getNodeConfig(conn.from.type);
    
    if (conn.type === 'spawn') {
      // Curved line from orchestrator down to subagent
      ctx.strokeStyle = config.color;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      
      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);
      const midX = (conn.from.x + conn.to.x) / 2;
      ctx.bezierCurveTo(
        midX, conn.from.y,
        midX, conn.to.y,
        conn.to.x, conn.to.y
      );
      ctx.stroke();
      ctx.setLineDash([]);
    } else if (conn.type === 'return') {
      // Curved line from subagent back up to orchestrator
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      
      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);
      const midX = (conn.from.x + conn.to.x) / 2;
      ctx.bezierCurveTo(
        midX, conn.from.y,
        midX, conn.to.y,
        conn.to.x, conn.to.y
      );
      ctx.stroke();
      ctx.setLineDash([]);
    } else if (conn.from.lane > 0) {
      // Subagent lane line
      ctx.strokeStyle = getNodeConfig(conn.from.type).color;
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      
      ctx.beginPath();
      ctx.moveTo(conn.from.x, conn.from.y);
      ctx.lineTo(conn.to.x, conn.to.y);
      ctx.stroke();
    }
  }
  
  // Draw nodes
  for (const node of nodes) {
    const config = getNodeConfig(node.type);
    const isHovered = hoveredNode.value === node.id;
    
    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, isHovered ? 18 : 14, 0, Math.PI * 2);
    ctx.fillStyle = config.color;
    ctx.fill();
    
    // Glow effect
    if (isHovered) {
      ctx.shadowColor = config.color;
      ctx.shadowBlur = 15;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    
    // Border
    ctx.strokeStyle = theme.value === 'dark' ? '#fff' : '#1f2937';
    ctx.lineWidth = isHovered ? 3 : 2;
    ctx.stroke();
    
    // Emoji
    ctx.font = isHovered ? '14px sans-serif' : '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#fff';
    ctx.fillText(config.emoji, node.x, node.y);
  }
  
  // Draw lane labels
  ctx.font = '11px sans-serif';
  ctx.fillStyle = textColor.value;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  
  const lanes = new Set(nodes.map(n => n.lane));
  for (const lane of lanes) {
    const y = 60 + lane * 50;
    const label = lane === 0 ? '🤖 Orchestrator' : `👥 Agent ${lane}`;
    ctx.fillText(label, 5, y);
  }
}

// Mouse event handlers
function handleMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value;
  if (!canvas) return;
  
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left + (containerRef.value?.scrollLeft || 0);
  const y = e.clientY - rect.top;
  
  // Check if hovering over a node
  let found = false;
  for (const node of flowData.value.nodes) {
    const dx = x - node.x;
    const dy = y - node.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    
    if (dist < 18) {
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
  
  // Handle drag
  if (isDragging.value && containerRef.value) {
    const dx = dragStartX.value - e.clientX;
    containerRef.value.scrollLeft = scrollOffset.value + dx;
  }
}

function handleMouseDown(e: MouseEvent) {
  // Check if clicking a node
  const canvas = canvasRef.value;
  if (!canvas) return;
  
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left + (containerRef.value?.scrollLeft || 0);
  const y = e.clientY - rect.top;
  
  for (const node of flowData.value.nodes) {
    const dx = x - node.x;
    const dy = y - node.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    
    if (dist < 18) {
      emit('nodeClick', node.id);
      return;
    }
  }
  
  // Start drag
  isDragging.value = true;
  dragStartX.value = e.clientX;
  scrollOffset.value = containerRef.value?.scrollLeft || 0;
}

function handleMouseUp() {
  isDragging.value = false;
}

function handleMouseLeave() {
  isDragging.value = false;
  hoveredNode.value = null;
  tooltipEvent.value = null;
}

// Watch for changes and redraw
watch([flowData, theme, hoveredNode], () => {
  draw();
}, { deep: true });

onMounted(() => {
  draw();
  
  // Update container width on resize
  const resizeObserver = new ResizeObserver(() => {
    if (containerRef.value) {
      containerWidth.value = containerRef.value.clientWidth;
    }
    draw();
  });
  
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value);
  }
});

// Format timestamp for tooltip
function formatTime(ts: number | undefined): string {
  if (!ts) return 'N/A';
  return new Date(ts).toLocaleTimeString();
}

// Get short message for tooltip
function getShortMessage(event: HookEvent): string {
  const payload = event.payload;
  if (payload.prompt) return String(payload.prompt).slice(0, 50) + '...';
  if (payload.thought) return String(payload.thought).slice(0, 50) + '...';
  if (payload.description) return String(payload.description).slice(0, 50) + '...';
  if (payload.message) return String(payload.message).slice(0, 50) + '...';
  if (payload.agent_type) return `Agent: ${payload.agent_type}`;
  return event.hook_event_type;
}
</script>

<template>
  <div class="card p-3">
    <!-- Header -->
    <div class="flex justify-between items-center mb-2">
      <span class="text-sm theme-text-secondary">🌳 Agent Flow</span>
      <div class="text-xs theme-text-muted">
        <span>{{ flowData.nodes.length }} events</span>
        <span class="mx-2">•</span>
        <span>Drag to pan →</span>
      </div>
    </div>
    
    <!-- Flow visualization container -->
    <div 
      ref="containerRef"
      class="relative overflow-x-auto overflow-y-hidden rounded cursor-grab active:cursor-grabbing"
      :class="isDragging ? 'cursor-grabbing' : 'cursor-grab'"
      @mousemove="handleMouseMove"
      @mousedown="handleMouseDown"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
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
          <div class="text-2xl mb-2">🌱</div>
          <div class="text-sm">No events yet</div>
          <div class="text-xs">Send a message to see the agent flow</div>
        </div>
      </div>
    </div>
    
    <!-- Tooltip -->
    <Teleport to="body">
      <div 
        v-if="tooltipEvent"
        class="fixed z-50 px-3 py-2 rounded-lg shadow-lg text-sm max-w-xs pointer-events-none"
        :class="theme === 'dark' ? 'bg-gray-800 text-white border border-gray-700' : 'bg-white text-gray-900 border border-gray-200'"
        :style="{ 
          left: `${tooltipPos.x + 15}px`, 
          top: `${tooltipPos.y - 10}px` 
        }"
      >
        <div class="font-medium flex items-center gap-2">
          <span>{{ getNodeConfig(tooltipEvent.hook_event_type).emoji }}</span>
          <span>{{ tooltipEvent.hook_event_type }}</span>
        </div>
        <div class="text-xs mt-1 opacity-70">{{ formatTime(tooltipEvent.timestamp) }}</div>
        <div class="text-xs mt-1 opacity-90">{{ getShortMessage(tooltipEvent) }}</div>
        <div class="text-xs mt-2 text-blue-400">Click to view in timeline</div>
      </div>
    </Teleport>
    
    <!-- Legend -->
    <div class="flex flex-wrap gap-3 mt-2 text-xs theme-text-muted">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-green-500"></span>
        <span>Orchestrator</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-amber-500"></span>
        <span>Subagent</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="inline-block w-4 border-t-2 border-dashed border-gray-400"></span>
        <span>Branch/Merge</span>
      </div>
    </div>
  </div>
</template>
