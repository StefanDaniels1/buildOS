<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  content: string;
}>();

// Parse markdown to HTML
const renderedHtml = computed(() => {
  let html = props.content || '';
  
  // Escape HTML to prevent XSS
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // Code blocks (triple backticks) - must be processed before inline code
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, _lang, code) => {
    return `<pre class="bg-black/30 p-3 rounded-lg overflow-x-auto my-3"><code class="text-sm font-mono">${code.trim()}</code></pre>`;
  });
  
  // Headers (must be at start of line)
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-5 mb-3">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-6 mb-4">$1</h1>');
  
  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-black/30 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');
  
  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr class="my-4 border-t border-current opacity-30" />');
  
  // Tables - more complex parsing
  html = parseMarkdownTables(html);
  
  // Numbered lists (e.g., "1. Item", "2. Item")
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal" value="$1">$2</li>');
  
  // Unordered lists (dash or asterisk)
  html = html.replace(/^[-*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');
  
  // Wrap consecutive list items in appropriate list tags
  html = html.replace(/(<li class="ml-4 list-decimal"[^>]*>.*?<\/li>\n?)+/g, '<ol class="my-2 space-y-1 pl-4">$&</ol>');
  html = html.replace(/(<li class="ml-4 list-disc">.*?<\/li>\n?)+/g, '<ul class="my-2 space-y-1 pl-4">$&</ul>');
  
  // Line breaks - convert double newlines to paragraphs
  html = html.replace(/\n\n+/g, '</p><p class="my-2">');
  
  // Single line breaks (but not inside block elements)
  html = html.replace(/\n/g, '<br/>');
  
  // Clean up: remove <br/> inside pre/code blocks
  html = html.replace(/<pre([^>]*)>([\s\S]*?)<\/pre>/g, (_match, attrs, content) => {
    return `<pre${attrs}>${content.replace(/<br\/>/g, '\n')}</pre>`;
  });
  
  // Wrap in paragraph if not starting with a block element
  if (!html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<ol') && !html.startsWith('<table') && !html.startsWith('<hr') && !html.startsWith('<pre')) {
    html = '<p class="my-2">' + html + '</p>';
  }
  
  return html;
});

function parseMarkdownTables(html: string): string {
  // Match markdown tables
  const tableRegex = /(\|.+\|[\r\n]+\|[-:| ]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)/g;
  
  return html.replace(tableRegex, (match) => {
    const lines = match.trim().split('\n').filter(line => line.trim());
    if (lines.length < 2) return match;
    
    // Parse header
    const headerCells = lines[0].split('|').filter(cell => cell.trim());
    
    // Skip separator line (lines[1])
    
    // Parse body rows
    const bodyRows = lines.slice(2).map(line => 
      line.split('|').filter(cell => cell.trim())
    );
    
    // Build HTML table
    let tableHtml = '<div class="overflow-x-auto my-4"><table class="min-w-full text-sm">';
    
    // Header
    tableHtml += '<thead><tr class="border-b border-current opacity-50">';
    headerCells.forEach(cell => {
      tableHtml += `<th class="px-3 py-2 text-left font-semibold">${cell.trim()}</th>`;
    });
    tableHtml += '</tr></thead>';
    
    // Body
    tableHtml += '<tbody>';
    bodyRows.forEach((row, idx) => {
      const rowClass = idx % 2 === 0 ? 'bg-black/10' : '';
      tableHtml += `<tr class="${rowClass}">`;
      row.forEach(cell => {
        tableHtml += `<td class="px-3 py-2">${cell.trim()}</td>`;
      });
      tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table></div>';
    
    return tableHtml;
  });
}
</script>

<template>
  <div class="markdown-content" v-html="renderedHtml" />
</template>

<style scoped>
.markdown-content {
  line-height: 1.6;
  color: inherit;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  color: inherit;
  line-height: 1.3;
}

.markdown-content :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-content :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
}

.markdown-content :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(p) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.markdown-content :deep(code) {
  word-break: break-word;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
  padding-left: 1.5rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
  padding-left: 1.5rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(li) {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

.markdown-content :deep(hr) {
  margin-top: 1rem;
  margin-bottom: 1rem;
  border-color: currentColor;
  opacity: 0.3;
}

.markdown-content :deep(a) {
  color: #10b981;
  text-decoration: underline;
}

.markdown-content :deep(a:hover) {
  color: #34d399;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid currentColor;
  padding-left: 1rem;
  margin-left: 0;
  opacity: 0.9;
  font-style: italic;
}
</style>
