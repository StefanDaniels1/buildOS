/**
 * Event Color Assignment Composable
 *
 * Deterministic color assignment based on hash for consistent coloring.
 */

// Color palette for sessions
const SESSION_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#14b8a6', // teal
  '#0ea5e9', // sky
  '#6366f1', // indigo
  '#a855f7', // purple
  '#ec4899', // pink
  '#f43f5e', // rose
];

// Event type colors
const EVENT_TYPE_COLORS: Record<string, string> = {
  SessionStart: '#22c55e',
  SessionEnd: '#ef4444',
  AgentThinking: '#0ea5e9',
  SubagentStart: '#a855f7',
  SubagentStop: '#6366f1',
  ToolStart: '#f97316',
  ToolStop: '#eab308',
  UserPromptSubmit: '#14b8a6',
  Stop: '#ec4899',
};

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

export function useEventColors() {
  function getSessionColor(sessionId: string): string {
    const index = hashString(sessionId) % SESSION_COLORS.length;
    return SESSION_COLORS[index];
  }

  function getEventTypeColor(eventType: string): string {
    return EVENT_TYPE_COLORS[eventType] || '#6b7280';
  }

  function getAppColor(appName: string): string {
    const hue = hashString(appName) % 360;
    return `hsl(${hue}, 70%, 50%)`;
  }

  return {
    getSessionColor,
    getEventTypeColor,
    getAppColor,
    SESSION_COLORS,
    EVENT_TYPE_COLORS
  };
}
