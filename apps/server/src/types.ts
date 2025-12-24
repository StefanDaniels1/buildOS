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
  user_id?: string; // User ID derived from API key hash (for session isolation)
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

// Custom MCP Tools
export interface CustomTool {
  id?: number;
  name: string;              // Tool name (alphanumeric + underscore)
  description: string;       // Description for Claude context
  input_schema: Record<string, string>; // Parameter schema {"param": "type"}
  handler_code: string;      // Python async function code
  enabled: boolean;          // Toggle for orchestrator
  env_vars: Record<string, string>; // Environment variables
  created_at?: number;
  updated_at?: number;
}

export interface ToolTestRequest {
  input: Record<string, unknown>;
  env_overrides?: Record<string, string>;
}

export interface ToolTestResult {
  success: boolean;
  output?: unknown;
  error?: string;
  duration_ms?: number;
}
