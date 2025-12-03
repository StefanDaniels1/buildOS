/**
 * WebSocket Event Broadcasting
 *
 * Manages WebSocket clients and broadcasts events to all connected clients.
 */

import type { HookEvent } from './types';
import { insertEvent } from './db';

// Store connected WebSocket clients
const wsClients = new Set<any>();

export function addClient(ws: any): void {
  wsClients.add(ws);
  console.log(`WebSocket client connected (${wsClients.size} total)`);
}

export function removeClient(ws: any): void {
  wsClients.delete(ws);
  console.log(`WebSocket client disconnected (${wsClients.size} total)`);
}

export function getClientCount(): number {
  return wsClients.size;
}

/**
 * Broadcast an event to all connected WebSocket clients.
 * Also saves the event to the database.
 */
export function broadcastEvent(event: HookEvent): HookEvent {
  // Save to database
  const savedEvent = insertEvent(event);

  // Broadcast to all clients
  const message = JSON.stringify({ type: 'event', data: savedEvent });
  wsClients.forEach(client => {
    try {
      client.send(message);
    } catch (err) {
      // Client disconnected, remove from set
      wsClients.delete(client);
    }
  });

  return savedEvent;
}

/**
 * Send initial events to a newly connected client.
 */
export function sendInitialEvents(ws: any, events: HookEvent[]): void {
  try {
    ws.send(JSON.stringify({ type: 'initial', data: events }));
  } catch (err) {
    console.error('Error sending initial events:', err);
  }
}
