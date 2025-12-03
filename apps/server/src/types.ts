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

export interface ChatRequest {
  message: string;
  session_id: string;
  file_path?: string;
  available_files?: string[]; // List of all available file paths
  api_key?: string; // User-provided Anthropic API key
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}
