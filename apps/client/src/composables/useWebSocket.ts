/**
 * WebSocket Connection Composable
 *
 * Manages WebSocket connection to dashboard server with auto-reconnect.
 */

import { ref, onMounted, onUnmounted } from 'vue';
import { WS_URL, MAX_EVENTS } from '../config';
import type { HookEvent } from '../types';

export function useWebSocket() {
  const events = ref<HookEvent[]>([]);
  const isConnected = ref(false);
  const error = ref<string | null>(null);

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;

  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return;

    console.log('Connecting to WebSocket:', WS_URL);
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      isConnected.value = true;
      error.value = null;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'initial') {
          // Initial batch of events
          events.value = message.data || [];
          console.log(`Received ${events.value.length} initial events`);
        } else if (message.type === 'event') {
          // New event
          events.value.push(message.data);
          // Trim to max events
          if (events.value.length > MAX_EVENTS) {
            events.value = events.value.slice(-MAX_EVENTS);
          }
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('WebSocket error:', e);
      error.value = 'Connection error';
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      isConnected.value = false;
      ws = null;

      // Auto-reconnect after 3 seconds
      reconnectTimeout = window.setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
      }, 3000);
    };
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  return {
    events,
    isConnected,
    error,
    connect,
    disconnect
  };
}
