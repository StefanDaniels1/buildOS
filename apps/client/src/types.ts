/**
 * buildOS Dashboard Types
 */

export interface HookEvent {
  id?: number;
  source_app: string;
  session_id: string;
  hook_event_type: string;
  payload: Record<string, unknown>;
  timestamp?: number;
  summary?: string;
}

export interface FilterOptions {
  source_apps: string[];
  session_ids: string[];
  hook_event_types: string[];
}

export interface UploadedFile {
  name: string;
  path: string;
  absolutePath: string;
  size: number;
  type: string;
  detectedType: string;
  uploadedAt: number;
}

export interface ChartDataPoint {
  timestamp: number;
  count: number;
  eventTypes: Record<string, number>;
  sessions: Record<string, number>;
}
