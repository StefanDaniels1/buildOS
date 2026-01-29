<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
// @ts-ignore - jspreadsheet-ce types are incomplete
import jspreadsheet from 'jspreadsheet-ce';
import 'jspreadsheet-ce/dist/jspreadsheet.css';
import { API_BASE_URL } from '../config';

// Type for jspreadsheet instance (using any due to incomplete type definitions)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type JSpreadsheetInstance = any;

// Props
const props = defineProps<{
  sessionId?: string | null;
  events?: Array<{
    hook_event_type: string;
    payload: any;
    session_id: string;
  }>;
}>();

// Emits
const emit = defineEmits<{
  (e: 'dataSaved', data: { name: string; data: any[][] }): void;
}>();

// Refs
const spreadsheetRef = ref<HTMLDivElement | null>(null);
const spreadsheetInstance = ref<JSpreadsheetInstance | null>(null);
const spreadsheetName = ref('Spreadsheet');
const isSaving = ref(false);
const isExporting = ref(false);
const lastSaved = ref<Date | null>(null);
const hasUnsavedChanges = ref(false);

// Default empty spreadsheet data
const defaultData = [
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
  ['', '', '', '', ''],
];

const defaultColumns = [
  { title: 'A', width: 120 },
  { title: 'B', width: 120 },
  { title: 'C', width: 120 },
  { title: 'D', width: 120 },
  { title: 'E', width: 120 },
];

// Initialize spreadsheet
function initSpreadsheet(data?: any[][], columns?: any[]) {
  if (!spreadsheetRef.value) return;

  // Destroy existing instance if any
  if (spreadsheetInstance.value) {
    // @ts-ignore - jspreadsheet types are incomplete
    jspreadsheet.destroy(spreadsheetRef.value as any);
    spreadsheetInstance.value = null;
  }

  // Create new instance
  spreadsheetInstance.value = jspreadsheet(spreadsheetRef.value, {
    data: data || defaultData,
    columns: columns || defaultColumns,
    minDimensions: [5, 10],
    tableOverflow: true,
    tableWidth: '100%',
    tableHeight: '100%',
    allowInsertRow: true,
    allowInsertColumn: true,
    allowDeleteRow: true,
    allowDeleteColumn: true,
    allowRenameColumn: true,
    columnSorting: true,
    columnDrag: true,
    columnResize: true,
    rowResize: true,
    search: true,
    onchange: () => {
      hasUnsavedChanges.value = true;
    },
    oninsertrow: () => {
      hasUnsavedChanges.value = true;
    },
    oninsertcolumn: () => {
      hasUnsavedChanges.value = true;
    },
    ondeleterow: () => {
      hasUnsavedChanges.value = true;
    },
    ondeletecolumn: () => {
      hasUnsavedChanges.value = true;
    },
  } as any);
}

// Load spreadsheet data from agent events
function loadFromEvents() {
  if (!props.events || !props.sessionId) return;

  // Find the most recent spreadsheet data in events
  // The agent returns spreadsheet data in the message field as JSON
  // Supports: Stop events, CSVLoaded events, AgentThinking with spreadsheet data
  const spreadsheetEvents = props.events
    .filter(e => {
      if (e.session_id !== props.sessionId) return false;

      // Support multiple event types that may contain spreadsheet data
      const validEventTypes = ['Stop', 'CSVLoaded', 'SpreadsheetReady'];

      // For Stop events, check status
      if (e.hook_event_type === 'Stop') {
        if (e.payload?.status !== 'success') return false;
      } else if (!validEventTypes.includes(e.hook_event_type)) {
        return false;
      }

      // Check if payload directly contains spreadsheet
      if (e.payload?.spreadsheet != null) return true;

      // Check if message contains spreadsheet data
      const message = e.payload?.message;
      if (typeof message === 'string') {
        try {
          const parsed = JSON.parse(message);
          return parsed?.spreadsheet || (parsed?.success && parsed?.spreadsheet);
        } catch {
          // Check if message mentions spreadsheet
          return message.includes('"spreadsheet"') || message.includes('"type": "spreadsheet"');
        }
      }
      return false;
    })
    .reverse();

  if (spreadsheetEvents.length > 0) {
    const event = spreadsheetEvents[0];
    let spreadsheetData = event.payload?.spreadsheet;

    // Try to parse from message if not directly available
    if (!spreadsheetData && event.payload?.message) {
      try {
        const parsed = JSON.parse(event.payload.message);
        spreadsheetData = parsed?.spreadsheet;
      } catch {
        // Not JSON, skip
      }
    }

    if (spreadsheetData) {
      loadSpreadsheetData(spreadsheetData);
    }
  }
}

// Import CSV from a file input
async function importCsv(file: File) {
  if (!file) return;

  const text = await file.text();
  const lines = text.split('\n').filter(line => line.trim());

  if (lines.length === 0) {
    alert('CSV file is empty');
    return;
  }

  // Detect delimiter
  const firstLine = lines[0];
  let delimiter = ',';
  if (firstLine.includes('\t')) delimiter = '\t';
  else if (firstLine.includes(';')) delimiter = ';';

  // Parse CSV
  const parseRow = (line: string) => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;

    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === delimiter && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const rows = lines.map(parseRow);
  const headers = rows[0];

  // Build columns
  const columns = headers.map(h => ({
    title: h,
    width: Math.min(Math.max(80, h.length * 10), 200)
  }));

  // Load into spreadsheet
  loadSpreadsheetData({
    name: file.name.replace(/\.[^.]+$/, ''),
    data: rows,
    columns
  });

  hasUnsavedChanges.value = true;
}

// Handle file drop/select for CSV import
function handleCsvUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file && (file.name.endsWith('.csv') || file.name.endsWith('.tsv'))) {
    importCsv(file);
  } else {
    alert('Please select a CSV or TSV file');
  }
  // Reset input so same file can be selected again
  input.value = '';
}

// Load spreadsheet data
function loadSpreadsheetData(spreadsheetData: any) {
  if (!spreadsheetData) return;

  const { name, data, columns } = spreadsheetData;

  if (name) {
    spreadsheetName.value = name;
  }

  // Convert columns to jspreadsheet format if needed
  const formattedColumns = columns?.map((col: any) => ({
    title: col.title || col,
    width: col.width || 120,
    type: col.type || 'text',
  })) || defaultColumns;

  initSpreadsheet(data || defaultData, formattedColumns);
  hasUnsavedChanges.value = false;
}

// Get current spreadsheet data
function getSpreadsheetData(): { name: string; data: any[][]; columns: any[] } {
  if (!spreadsheetInstance.value) {
    return { name: spreadsheetName.value, data: defaultData, columns: defaultColumns };
  }

  const data = spreadsheetInstance.value.getData();
  const headers = spreadsheetInstance.value.getHeaders(true);

  return {
    name: spreadsheetName.value,
    data: data,
    columns: headers.map((h: string) => ({
      title: h,
      width: 120,
    })),
  };
}

// Save spreadsheet to session context
async function saveSpreadsheet() {
  if (!props.sessionId) {
    alert('No active session. Please start a conversation first.');
    return;
  }

  isSaving.value = true;

  try {
    const spreadsheetData = getSpreadsheetData();

    const response = await fetch(`${API_BASE_URL}/api/spreadsheet/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: props.sessionId,
        spreadsheet: spreadsheetData,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to save spreadsheet');
    }

    lastSaved.value = new Date();
    hasUnsavedChanges.value = false;
    emit('dataSaved', spreadsheetData);
  } catch (error) {
    console.error('Error saving spreadsheet:', error);
    alert('Failed to save spreadsheet. Please try again.');
  } finally {
    isSaving.value = false;
  }
}

// Clear spreadsheet
function clearSpreadsheet() {
  if (confirm('Are you sure you want to clear the spreadsheet?')) {
    initSpreadsheet(defaultData, defaultColumns);
    spreadsheetName.value = 'Spreadsheet';
    hasUnsavedChanges.value = true;
  }
}

// Export to CSV
function exportToCsv() {
  if (!spreadsheetInstance.value) return;

  const csv = spreadsheetInstance.value.copy(false, ',', true);
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${spreadsheetName.value.replace(/\s+/g, '_')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// Export to Excel via API
async function exportToExcel() {
  if (!props.sessionId) {
    alert('No active session. Please start a conversation first.');
    return;
  }

  isExporting.value = true;

  try {
    const spreadsheetData = getSpreadsheetData();

    // Call the chat API to trigger Excel generation
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `Export the current spreadsheet "${spreadsheetData.name}" to a downloadable Excel file. The data is: ${JSON.stringify(spreadsheetData.data)}`,
        session_id: props.sessionId,
        api_key: localStorage.getItem('buildos_api_key'),
        user_id: localStorage.getItem('buildos_user_id'),
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to trigger Excel export');
    }

    alert('Excel export started! Check the chat for the download link.');
  } catch (error) {
    console.error('Error exporting to Excel:', error);
    alert('Failed to export to Excel. Please try again.');
  } finally {
    isExporting.value = false;
  }
}

// Watch for event changes to load spreadsheet data
watch(() => props.events, () => {
  loadFromEvents();
}, { deep: true });

// Initialize on mount
onMounted(async () => {
  await nextTick();
  initSpreadsheet();
  loadFromEvents();
});

// Cleanup on unmount
onUnmounted(() => {
  if (spreadsheetRef.value && spreadsheetInstance.value) {
    // @ts-ignore - jspreadsheet types are incomplete
    jspreadsheet.destroy(spreadsheetRef.value as any);
  }
});

// Expose methods for parent component
defineExpose({
  loadSpreadsheetData,
  getSpreadsheetData,
  saveSpreadsheet,
});
</script>

<template>
  <div class="flex flex-col h-full theme-surface rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between p-3 border-b theme-border">
      <div class="flex items-center gap-3">
        <input
          v-model="spreadsheetName"
          type="text"
          class="input-field text-sm font-medium w-48"
          placeholder="Spreadsheet name"
          @change="hasUnsavedChanges = true"
        />
        <span v-if="hasUnsavedChanges" class="text-xs text-yellow-500">
          Unsaved changes
        </span>
        <span v-else-if="lastSaved" class="text-xs theme-text-muted">
          Saved {{ lastSaved.toLocaleTimeString() }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Import CSV button -->
        <label
          class="px-3 py-1.5 text-sm theme-text-secondary hover:theme-text cursor-pointer transition-colors"
          title="Import CSV file"
        >
          Import
          <input
            type="file"
            accept=".csv,.tsv"
            class="hidden"
            @change="handleCsvUpload"
          />
        </label>
        <span class="text-xs theme-text-muted">|</span>
        <button
          @click="exportToCsv"
          class="px-3 py-1.5 text-sm theme-text-secondary hover:theme-text transition-colors"
          title="Export to CSV"
        >
          CSV
        </button>
        <button
          @click="exportToExcel"
          :disabled="isExporting"
          class="px-3 py-1.5 text-sm theme-text-secondary hover:theme-text disabled:opacity-50 transition-colors"
          title="Export to Excel (.xlsx)"
        >
          {{ isExporting ? 'Exporting...' : 'Excel' }}
        </button>
        <button
          @click="clearSpreadsheet"
          class="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 transition-colors"
          title="Clear spreadsheet"
        >
          Clear
        </button>
        <button
          @click="saveSpreadsheet"
          :disabled="isSaving || !hasUnsavedChanges"
          class="px-4 py-1.5 text-sm bg-buildos-primary hover:bg-buildos-secondary disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>

    <!-- Spreadsheet container -->
    <div class="flex-1 overflow-auto p-2">
      <div ref="spreadsheetRef" class="jspreadsheet-container"></div>
    </div>

    <!-- Footer with instructions -->
    <div class="p-2 border-t theme-border text-xs theme-text-muted">
      <p>
        <strong>CSV Agent:</strong> Upload a CSV or ask the agent to load/analyze data. Use <strong>Import</strong> for direct CSV upload, or ask "load my CSV file" to process uploaded files. <strong>Save</strong> to preserve edits for follow-up requests.
      </p>
    </div>
  </div>
</template>

<style>
/* jspreadsheet theme customization */
.jspreadsheet-container {
  width: 100%;
  height: 100%;
}

.jexcel {
  font-family: inherit;
}

.jexcel thead td {
  background-color: var(--color-surface, #1e293b) !important;
  color: var(--color-text, #e2e8f0) !important;
  border-color: var(--color-border, #334155) !important;
}

.jexcel tbody td {
  background-color: var(--color-bg, #0f172a) !important;
  color: var(--color-text, #e2e8f0) !important;
  border-color: var(--color-border, #334155) !important;
}

.jexcel tbody td:hover {
  background-color: var(--color-surface, #1e293b) !important;
}

.jexcel tbody td.selected {
  background-color: rgba(59, 130, 246, 0.2) !important;
}

.jexcel_content {
  background-color: var(--color-bg, #0f172a) !important;
}

.jexcel_toolbar {
  background-color: var(--color-surface, #1e293b) !important;
  border-color: var(--color-border, #334155) !important;
}

/* Light theme support */
[data-theme="light"] .jexcel thead td {
  background-color: #f1f5f9 !important;
  color: #1e293b !important;
  border-color: #e2e8f0 !important;
}

[data-theme="light"] .jexcel tbody td {
  background-color: #ffffff !important;
  color: #1e293b !important;
  border-color: #e2e8f0 !important;
}

[data-theme="light"] .jexcel tbody td:hover {
  background-color: #f8fafc !important;
}

[data-theme="light"] .jexcel_content {
  background-color: #ffffff !important;
}
</style>
