/**
 * useTools Composable
 *
 * Provides reactive state and API methods for managing custom MCP tools.
 */

import { ref, computed } from 'vue';
import { API_BASE_URL } from '../config';

export interface CustomTool {
  id?: number;
  name: string;
  description: string;
  input_schema: Record<string, string>;
  handler_code: string;
  enabled: boolean;
  env_vars: Record<string, string>;
  created_at?: number;
  updated_at?: number;
}

export interface ToolTemplate {
  name: string;
  description: string;
  input_schema: Record<string, string>;
  handler_code: string;
  env_vars: Record<string, string>;
}

// Shared state (singleton pattern)
const tools = ref<CustomTool[]>([]);
const templates = ref<ToolTemplate[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

export function useTools() {
  // Computed properties
  const enabledTools = computed(() => tools.value.filter(t => t.enabled));
  const disabledTools = computed(() => tools.value.filter(t => !t.enabled));
  const toolCount = computed(() => tools.value.length);
  const enabledCount = computed(() => enabledTools.value.length);

  // Fetch all tools
  async function fetchTools(): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools`);
      const data = await response.json();

      if (data.success) {
        tools.value = data.tools;
      } else {
        error.value = data.error || 'Failed to fetch tools';
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Network error';
    } finally {
      isLoading.value = false;
    }
  }

  // Fetch tool templates
  async function fetchTemplates(): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/templates`);
      const data = await response.json();

      if (data.success) {
        templates.value = data.templates;
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  }

  // Create a new tool
  async function createTool(tool: Omit<CustomTool, 'id' | 'created_at' | 'updated_at'>): Promise<CustomTool | null> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
      });
      const data = await response.json();

      if (data.success) {
        tools.value = [data.tool, ...tools.value];
        return data.tool;
      } else {
        error.value = data.error || 'Failed to create tool';
        return null;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Network error';
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  // Update an existing tool
  async function updateTool(id: number, updates: Partial<CustomTool>): Promise<CustomTool | null> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      const data = await response.json();

      if (data.success) {
        const index = tools.value.findIndex(t => t.id === id);
        if (index !== -1) {
          tools.value[index] = data.tool;
        }
        return data.tool;
      } else {
        error.value = data.error || 'Failed to update tool';
        return null;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Network error';
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  // Delete a tool
  async function deleteTool(id: number): Promise<boolean> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/${id}`, {
        method: 'DELETE'
      });
      const data = await response.json();

      if (data.success) {
        tools.value = tools.value.filter(t => t.id !== id);
        return true;
      } else {
        error.value = data.error || 'Failed to delete tool';
        return false;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Network error';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  // Toggle tool enabled/disabled
  async function toggleTool(id: number): Promise<CustomTool | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/${id}/toggle`, {
        method: 'PATCH'
      });
      const data = await response.json();

      if (data.success) {
        const index = tools.value.findIndex(t => t.id === id);
        if (index !== -1) {
          tools.value[index] = data.tool;
        }
        return data.tool;
      } else {
        error.value = data.error || 'Failed to toggle tool';
        return null;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Network error';
      return null;
    }
  }

  // Get a tool by ID
  function getToolById(id: number): CustomTool | undefined {
    return tools.value.find(t => t.id === id);
  }

  // Clear error
  function clearError(): void {
    error.value = null;
  }

  return {
    // State
    tools,
    templates,
    isLoading,
    error,

    // Computed
    enabledTools,
    disabledTools,
    toolCount,
    enabledCount,

    // Methods
    fetchTools,
    fetchTemplates,
    createTool,
    updateTool,
    deleteTool,
    toggleTool,
    getToolById,
    clearError
  };
}
