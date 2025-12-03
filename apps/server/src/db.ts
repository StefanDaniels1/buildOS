/**
 * buildOS Dashboard Database
 *
 * SQLite database for storing events with proper indexing.
 */

import { Database } from 'bun:sqlite';
import type { HookEvent, FilterOptions } from './types';

let db: Database;

export function initDatabase(): void {
  const dbPath = process.env.DB_PATH || 'events.db';
  db = new Database(dbPath);

  // Enable WAL mode for better concurrent access
  db.run('PRAGMA journal_mode = WAL');

  // Create events table
  db.run(`
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_app TEXT NOT NULL,
      session_id TEXT NOT NULL,
      hook_event_type TEXT NOT NULL,
      payload TEXT NOT NULL,
      summary TEXT,
      timestamp INTEGER NOT NULL
    )
  `);

  // Create indexes for common queries
  db.run('CREATE INDEX IF NOT EXISTS idx_source_app ON events(source_app)');
  db.run('CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)');
  db.run('CREATE INDEX IF NOT EXISTS idx_hook_event_type ON events(hook_event_type)');
  db.run('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)');

  console.log('Database initialized');
}

export function insertEvent(event: HookEvent): HookEvent {
  const timestamp = event.timestamp || Date.now();
  const payload = JSON.stringify(event.payload);

  const stmt = db.prepare(`
    INSERT INTO events (source_app, session_id, hook_event_type, payload, summary, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    event.source_app,
    event.session_id,
    event.hook_event_type,
    payload,
    event.summary || null,
    timestamp
  );

  return {
    ...event,
    id: Number(result.lastInsertRowid),
    timestamp,
    payload: event.payload
  };
}

export function getRecentEvents(limit: number = 300): HookEvent[] {
  const stmt = db.prepare(`
    SELECT * FROM events
    ORDER BY timestamp DESC
    LIMIT ?
  `);

  const rows = stmt.all(limit) as Array<{
    id: number;
    source_app: string;
    session_id: string;
    hook_event_type: string;
    payload: string;
    summary: string | null;
    timestamp: number;
  }>;

  return rows.map(row => ({
    id: row.id,
    source_app: row.source_app,
    session_id: row.session_id,
    hook_event_type: row.hook_event_type,
    payload: JSON.parse(row.payload),
    summary: row.summary || undefined,
    timestamp: row.timestamp
  })).reverse(); // Return in chronological order
}

export function getFilterOptions(): FilterOptions {
  const sourceApps = db.prepare('SELECT DISTINCT source_app FROM events').all() as Array<{ source_app: string }>;
  const sessionIds = db.prepare('SELECT DISTINCT session_id FROM events ORDER BY session_id DESC LIMIT 50').all() as Array<{ session_id: string }>;
  const eventTypes = db.prepare('SELECT DISTINCT hook_event_type FROM events').all() as Array<{ hook_event_type: string }>;

  return {
    source_apps: sourceApps.map(r => r.source_app),
    session_ids: sessionIds.map(r => r.session_id),
    hook_event_types: eventTypes.map(r => r.hook_event_type)
  };
}

export function clearEvents(): void {
  db.run('DELETE FROM events');
  console.log('All events cleared');
}
