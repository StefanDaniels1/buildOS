/**
 * buildOS Dashboard Database
 *
 * SQLite database for storing events with proper indexing.
 */

import { Database } from 'bun:sqlite';
import type { HookEvent, FilterOptions, CustomTool } from './types';

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

  // Create custom_tools table for MCP tools builder
  db.run(`
    CREATE TABLE IF NOT EXISTS custom_tools (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      description TEXT NOT NULL,
      input_schema TEXT NOT NULL,
      handler_code TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1,
      env_vars TEXT NOT NULL DEFAULT '{}',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )
  `);

  db.run('CREATE INDEX IF NOT EXISTS idx_custom_tools_enabled ON custom_tools(enabled)');

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

// Custom Tools CRUD Operations

export function getAllTools(): CustomTool[] {
  const stmt = db.prepare('SELECT * FROM custom_tools ORDER BY created_at DESC');
  const rows = stmt.all() as Array<{
    id: number;
    name: string;
    description: string;
    input_schema: string;
    handler_code: string;
    enabled: number;
    env_vars: string;
    created_at: number;
    updated_at: number;
  }>;

  return rows.map(row => ({
    id: row.id,
    name: row.name,
    description: row.description,
    input_schema: JSON.parse(row.input_schema),
    handler_code: row.handler_code,
    enabled: row.enabled === 1,
    env_vars: JSON.parse(row.env_vars),
    created_at: row.created_at,
    updated_at: row.updated_at
  }));
}

export function getEnabledTools(): CustomTool[] {
  const stmt = db.prepare('SELECT * FROM custom_tools WHERE enabled = 1 ORDER BY name');
  const rows = stmt.all() as Array<{
    id: number;
    name: string;
    description: string;
    input_schema: string;
    handler_code: string;
    enabled: number;
    env_vars: string;
    created_at: number;
    updated_at: number;
  }>;

  return rows.map(row => ({
    id: row.id,
    name: row.name,
    description: row.description,
    input_schema: JSON.parse(row.input_schema),
    handler_code: row.handler_code,
    enabled: true,
    env_vars: JSON.parse(row.env_vars),
    created_at: row.created_at,
    updated_at: row.updated_at
  }));
}

export function getToolById(id: number): CustomTool | null {
  const stmt = db.prepare('SELECT * FROM custom_tools WHERE id = ?');
  const row = stmt.get(id) as {
    id: number;
    name: string;
    description: string;
    input_schema: string;
    handler_code: string;
    enabled: number;
    env_vars: string;
    created_at: number;
    updated_at: number;
  } | null;

  if (!row) return null;

  return {
    id: row.id,
    name: row.name,
    description: row.description,
    input_schema: JSON.parse(row.input_schema),
    handler_code: row.handler_code,
    enabled: row.enabled === 1,
    env_vars: JSON.parse(row.env_vars),
    created_at: row.created_at,
    updated_at: row.updated_at
  };
}

export function createTool(tool: CustomTool): CustomTool {
  const now = Date.now();
  const stmt = db.prepare(`
    INSERT INTO custom_tools (name, description, input_schema, handler_code, enabled, env_vars, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    tool.name,
    tool.description,
    JSON.stringify(tool.input_schema),
    tool.handler_code,
    tool.enabled ? 1 : 0,
    JSON.stringify(tool.env_vars || {}),
    now,
    now
  );

  return {
    ...tool,
    id: Number(result.lastInsertRowid),
    created_at: now,
    updated_at: now
  };
}

export function updateTool(id: number, tool: Partial<CustomTool>): CustomTool | null {
  const existing = getToolById(id);
  if (!existing) return null;

  const now = Date.now();
  const updated = {
    ...existing,
    ...tool,
    updated_at: now
  };

  const stmt = db.prepare(`
    UPDATE custom_tools
    SET name = ?, description = ?, input_schema = ?, handler_code = ?, enabled = ?, env_vars = ?, updated_at = ?
    WHERE id = ?
  `);

  stmt.run(
    updated.name,
    updated.description,
    JSON.stringify(updated.input_schema),
    updated.handler_code,
    updated.enabled ? 1 : 0,
    JSON.stringify(updated.env_vars || {}),
    now,
    id
  );

  return updated;
}

export function deleteTool(id: number): boolean {
  const stmt = db.prepare('DELETE FROM custom_tools WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}

export function toggleTool(id: number): CustomTool | null {
  const existing = getToolById(id);
  if (!existing) return null;

  const now = Date.now();
  const newEnabled = !existing.enabled;

  const stmt = db.prepare('UPDATE custom_tools SET enabled = ?, updated_at = ? WHERE id = ?');
  stmt.run(newEnabled ? 1 : 0, now, id);

  return {
    ...existing,
    enabled: newEnabled,
    updated_at: now
  };
}
