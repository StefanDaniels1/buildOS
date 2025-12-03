/**
 * Event Emoji Mapping Composable
 */

const EVENT_EMOJIS: Record<string, string> = {
  SessionStart: '🚀',
  SessionEnd: '🏁',
  AgentThinking: '🧠',
  SubagentStart: '👥',
  SubagentStop: '✅',
  ToolStart: '🔧',
  ToolStop: '✨',
  UserPromptSubmit: '💬',
  Stop: '🛑',
  PreToolUse: '🔧',
  PostToolUse: '✅',
  AgentMetrics: '📊',
};

export function useEventEmojis() {
  function getEmoji(eventType: string): string {
    return EVENT_EMOJIS[eventType] || '📌';
  }

  return {
    getEmoji,
    EVENT_EMOJIS
  };
}
