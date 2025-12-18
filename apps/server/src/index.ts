/**
 * buildOS Dashboard Server
 *
 * Bun server providing:
 * - POST /events - Receive events from orchestrator and hooks
 * - GET /events/recent - Get recent events
 * - GET /events/filter-options - Get filter options
 * - POST /api/upload - File uploads
 * - POST /api/chat - Trigger orchestrator
 * - WS /stream - WebSocket event streaming
 */

import { initDatabase, getRecentEvents, getFilterOptions, insertEvent, clearEvents } from './db';
import { addClient, removeClient, sendInitialEvents, broadcastEvent } from './websocket';
import { triggerOrchestrator } from './orchestrator';
import type { HookEvent, ChatRequest, UploadedFile } from './types';

// Initialize database
initDatabase();

const PORT = parseInt(process.env.SERVER_PORT || '4000');

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// Create server
const server = Bun.serve({
  port: PORT,

  async fetch(req: Request) {
    const url = new URL(req.url);

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // ==================== EVENT ENDPOINTS ====================

    // POST /events - Receive events from orchestrator/hooks
    if (url.pathname === '/events' && req.method === 'POST') {
      try {
        const event: HookEvent = await req.json();

        // Validate required fields
        if (!event.source_app || !event.session_id || !event.hook_event_type || !event.payload) {
          return new Response(JSON.stringify({ error: 'Missing required fields' }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Save and broadcast event
        const savedEvent = broadcastEvent(event);

        return new Response(JSON.stringify(savedEvent), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error processing event:', error);
        return new Response(JSON.stringify({ error: 'Invalid request' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /events/recent - Get recent events
    if (url.pathname === '/events/recent' && req.method === 'GET') {
      const limit = parseInt(url.searchParams.get('limit') || '300');
      const events = getRecentEvents(limit);
      return new Response(JSON.stringify(events), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // GET /events/filter-options - Get available filter options
    if (url.pathname === '/events/filter-options' && req.method === 'GET') {
      const options = getFilterOptions();
      return new Response(JSON.stringify(options), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // DELETE /events - Clear all events
    if (url.pathname === '/events' && req.method === 'DELETE') {
      clearEvents();
      return new Response(JSON.stringify({ success: true, message: 'All events cleared' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // ==================== UPLOAD ENDPOINT ====================

    // POST /api/upload - Handle file uploads
    if (url.pathname === '/api/upload' && req.method === 'POST') {
      try {
        const formData = await req.formData();
        const file = formData.get('file') as File;

        if (!file) {
          return new Response(JSON.stringify({
            success: false,
            error: 'No file provided'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Uploads directory (project root/uploads)
        let uploadsDir = process.cwd();
        if (uploadsDir.includes('/apps/server')) {
          uploadsDir = uploadsDir.replace('/apps/server', '') + '/uploads';
        } else if (uploadsDir.includes('/apps')) {
          uploadsDir = uploadsDir.replace('/apps', '') + '/uploads';
        } else {
          uploadsDir = uploadsDir + '/uploads';
        }

        // Ensure directory exists
        await Bun.write(`${uploadsDir}/.gitkeep`, '');

        // Save file with timestamp
        const timestamp = Date.now();
        const sanitizedName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
        const filename = `${timestamp}_${sanitizedName}`;
        const filepath = `${uploadsDir}/${filename}`;
        const relativePath = `uploads/${filename}`;

        await Bun.write(filepath, file);

        console.log(`File uploaded: ${relativePath} (${file.size} bytes)`);

        // Detect file type
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        let detectedType = 'unknown';
        if (ext === 'ifc') detectedType = 'ifc';
        else if (['csv', 'xlsx', 'xls'].includes(ext)) detectedType = 'spreadsheet';
        else if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(ext)) detectedType = 'image';
        else if (ext === 'pdf') detectedType = 'pdf';

        const uploadedFile: UploadedFile = {
          name: file.name,
          path: relativePath,
          absolutePath: filepath,
          size: file.size,
          type: file.type,
          detectedType,
          uploadedAt: timestamp
        };

        return new Response(JSON.stringify({
          success: true,
          file: uploadedFile
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error uploading file:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Upload failed'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // ==================== CHAT ENDPOINT ====================

    // POST /api/chat - Send message to orchestrator
    if (url.pathname === '/api/chat' && req.method === 'POST') {
      try {
        const body: ChatRequest = await req.json();
        const { message, session_id, file_path, available_files, api_key, user_id } = body;

        // DEBUG: Log received request (never log actual API key)
        console.log('📨 /api/chat received:', {
          message: message?.substring(0, 50),
          session_id,
          file_path,
          available_files_count: available_files?.length || 0,
          has_api_key: !!api_key,
          user_id: user_id || 'none'
        });

        if (!message || !session_id) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Message and session_id are required'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // SECURITY: Require user_id for session isolation
        if (!user_id || user_id.length < 8) {
          return new Response(JSON.stringify({
            success: false,
            error: 'User identification required. Please refresh the page and enter your API key.'
          }), {
            status: 401,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // SECURITY: Only use user-provided API key - never fall back to server key
        // This ensures each user pays for their own usage and keys stay isolated
        if (!api_key) {
          return new Response(JSON.stringify({
            success: false,
            error: 'API key required. Please click "Set API Key" and enter your Anthropic API key. Get one at console.anthropic.com'
          }), {
            status: 401,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Validate API key format (basic check)
        if (!api_key.startsWith('sk-ant-')) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Invalid API key format. Anthropic keys start with "sk-ant-"'
          }), {
            status: 401,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        const anthropicApiKey = api_key;

        // Trigger orchestrator in background with user_id for session isolation
        triggerOrchestrator(message, session_id, file_path, available_files, anthropicApiKey, user_id).catch((err: Error) => {
          console.error('Orchestrator error:', err);
        });

        return new Response(JSON.stringify({
          success: true,
          message: 'Orchestrator started',
          session_id
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error processing chat:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Invalid request'
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // ==================== SESSION LOG ENDPOINTS ====================

    // GET /api/sessions - Get list of recent session logs
    if (url.pathname === '/api/sessions' && req.method === 'GET') {
      try {
        const limit = parseInt(url.searchParams.get('limit') || '20');
        
        // Find project root and logs directory
        let projectRoot = process.cwd();
        if (projectRoot.includes('/apps/server')) {
          projectRoot = projectRoot.replace('/apps/server', '');
        } else if (projectRoot.includes('/apps')) {
          projectRoot = projectRoot.replace('/apps', '');
        }
        
        const logsDir = `${projectRoot}/.logs/conversations`;
        const dir = Bun.file(logsDir);
        
        // Read directory to get session files
        const sessions: any[] = [];
        try {
          const files = await Array.fromAsync(
            (await Bun.file(`${logsDir}/.`).text()).split('\n')
          );
          
          // In Bun, we need to use a different approach to list files
          // Let's use a shell command instead
          const proc = Bun.spawn(['ls', '-t', logsDir], { stdout: 'pipe' });
          const output = await new Response(proc.stdout).text();
          const logFiles = output.split('\n').filter(f => f.endsWith('.jsonl')).slice(0, limit);
          
          for (const filename of logFiles) {
            const filepath = `${logsDir}/${filename}`;
            const file = Bun.file(filepath);
            const text = await file.text();
            const lines = text.trim().split('\n');
            
            if (lines.length > 0) {
              const firstEvent = JSON.parse(lines[0]);
              const lastEvent = JSON.parse(lines[lines.length - 1]);
              
              sessions.push({
                session_id: firstEvent.session_id,
                start_time: firstEvent.timestamp,
                end_time: lastEvent.timestamp,
                event_count: lines.length,
                log_file: filename,
                status: lastEvent.event === 'session_end' ? lastEvent.status : 'ongoing'
              });
            }
          }
        } catch (e) {
          console.log('No session logs found or error reading logs:', e);
        }
        
        return new Response(JSON.stringify({
          success: true,
          sessions
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error fetching sessions:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to fetch sessions'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /api/sessions/:sessionId - Get full session log
    if (url.pathname.startsWith('/api/sessions/') && req.method === 'GET') {
      try {
        const sessionId = url.pathname.replace('/api/sessions/', '');
        
        // Find project root and logs directory
        let projectRoot = process.cwd();
        if (projectRoot.includes('/apps/server')) {
          projectRoot = projectRoot.replace('/apps/server', '');
        } else if (projectRoot.includes('/apps')) {
          projectRoot = projectRoot.replace('/apps', '');
        }
        
        const logsDir = `${projectRoot}/.logs/conversations`;
        const pattern = `session_${sessionId.slice(0, 8)}_`;
        
        // Find matching log file
        const proc = Bun.spawn(['ls', logsDir], { stdout: 'pipe' });
        const output = await new Response(proc.stdout).text();
        const logFiles = output.split('\n').filter(f => f.startsWith(pattern) && f.endsWith('.jsonl'));
        
        if (logFiles.length === 0) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Session log not found'
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }
        
        // Read the most recent matching file
        const filepath = `${logsDir}/${logFiles[0]}`;
        const file = Bun.file(filepath);
        const text = await file.text();
        const events = text.trim().split('\n').map(line => JSON.parse(line));
        
        return new Response(JSON.stringify({
          success: true,
          session_id: sessionId,
          events
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error fetching session log:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to fetch session log'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // ==================== STATIC FILES (uploads) ====================

    // GET /uploads/* - Serve uploaded files
    if (url.pathname.startsWith('/uploads/') && req.method === 'GET') {
      try {
        const filename = url.pathname.replace('/uploads/', '');
        
        // Use process.cwd() to find uploads directory
        let uploadsDir = process.cwd();
        if (uploadsDir.includes('/apps/server')) {
          uploadsDir = uploadsDir.replace('/apps/server', '') + '/uploads';
        } else if (uploadsDir.includes('/apps')) {
          uploadsDir = uploadsDir.replace('/apps', '') + '/uploads';
        } else {
          uploadsDir = uploadsDir + '/uploads';
        }
        
        const filepath = `${uploadsDir}/${filename}`;

        console.log('Serving file request:', { pathname: url.pathname, filename, uploadsDir, filepath });

        const file = Bun.file(filepath);
        const exists = await file.exists();
        console.log('File exists:', exists);

        if (exists) {
          // Determine content type
          const ext = filename.split('.').pop()?.toLowerCase() || '';
          let contentType = 'application/octet-stream';
          if (ext === 'ifc') contentType = 'application/x-step';
          else if (ext === 'json') contentType = 'application/json';
          else if (ext === 'csv') contentType = 'text/csv';
          else if (ext === 'pdf') contentType = 'application/pdf';
          else if (ext === 'xlsx') contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          else if (ext === 'xls') contentType = 'application/vnd.ms-excel';
          else if (ext === 'pptx') contentType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
          else if (ext === 'ppt') contentType = 'application/vnd.ms-powerpoint';
          else if (ext === 'docx') contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          else if (ext === 'doc') contentType = 'application/msword';

          return new Response(file, {
            headers: {
              ...corsHeaders,
              'Content-Type': contentType,
              'Content-Disposition': `inline; filename="${filename}"`
            }
          });
        } else {
          return new Response(JSON.stringify({ error: 'File not found' }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }
      } catch (error) {
        console.error('Error serving file:', error);
        return new Response(JSON.stringify({ error: 'Failed to serve file' }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /workspace/* - Serve workspace files (generated reports, etc.)
    // SECURITY: Files are isolated by user_id in path: .context/{user_id}/session_xxx/
    if (url.pathname.startsWith('/workspace/') && req.method === 'GET') {
      try {
        const relativePath = url.pathname.replace('/workspace/', '');

        // SECURITY: Prevent path traversal attacks
        if (relativePath.includes('..') || relativePath.includes('//')) {
          console.warn('Security: Blocked path traversal attempt:', relativePath);
          return new Response(JSON.stringify({ error: 'Invalid path' }), {
            status: 403,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // SECURITY: Only allow access to .context/ files (user session data)
        // or uploads/ (shared uploaded files)
        if (!relativePath.startsWith('.context/') && !relativePath.startsWith('uploads/')) {
          console.warn('Security: Blocked access to unauthorized path:', relativePath);
          return new Response(JSON.stringify({ error: 'Access denied' }), {
            status: 403,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Use process.cwd() to find workspace directory
        let workspaceDir = process.cwd();
        if (workspaceDir.includes('/apps/server')) {
          workspaceDir = workspaceDir.replace('/apps/server', '') + '/workspace';
        } else if (workspaceDir.includes('/apps')) {
          workspaceDir = workspaceDir.replace('/apps', '') + '/workspace';
        } else {
          workspaceDir = workspaceDir + '/workspace';
        }

        const filepath = `${workspaceDir}/${relativePath}`;

        console.log('Serving workspace file:', { relativePath });

        const file = Bun.file(filepath);
        const exists = await file.exists();
        console.log('Workspace file exists:', exists);

        if (exists) {
          // Determine content type based on extension
          const ext = relativePath.split('.').pop()?.toLowerCase() || '';
          let contentType = 'application/octet-stream';
          let disposition = 'inline';
          
          if (ext === 'ifc') contentType = 'application/x-step';
          else if (ext === 'json') contentType = 'application/json';
          else if (ext === 'csv') contentType = 'text/csv';
          else if (ext === 'pdf') contentType = 'application/pdf';
          else if (ext === 'xlsx') {
            contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
            disposition = 'attachment';  // Force download for Excel
          }
          else if (ext === 'xls') {
            contentType = 'application/vnd.ms-excel';
            disposition = 'attachment';
          }
          else if (ext === 'pptx') {
            contentType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
            disposition = 'attachment';  // Force download for PowerPoint
          }
          else if (ext === 'ppt') {
            contentType = 'application/vnd.ms-powerpoint';
            disposition = 'attachment';
          }
          else if (ext === 'docx') {
            contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
            disposition = 'attachment';  // Force download for Word
          }
          else if (ext === 'doc') {
            contentType = 'application/msword';
            disposition = 'attachment';
          }
          else if (ext === 'txt') contentType = 'text/plain';
          else if (ext === 'html') contentType = 'text/html';

          // Extract just the filename for disposition
          const filename = relativePath.split('/').pop() || relativePath;

          return new Response(file, {
            headers: {
              ...corsHeaders,
              'Content-Type': contentType,
              'Content-Disposition': `${disposition}; filename="${filename}"`
            }
          });
        } else {
          return new Response(JSON.stringify({ error: 'File not found' }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }
      } catch (error) {
        console.error('Error serving workspace file:', error);
        return new Response(JSON.stringify({ error: 'Failed to serve file' }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // ==================== WEBSOCKET ====================

    // WebSocket upgrade
    if (url.pathname === '/stream') {
      const success = server.upgrade(req);
      if (success) {
        return undefined;
      }
    }

    // ==================== STATIC FILES ====================
    
    // Serve static frontend files (always serve if dist exists)
    {
      let staticPath = url.pathname;
      if (staticPath === '/') staticPath = '/index.html';
      
      // Try to find the static file
      let projectRoot = process.cwd();
      if (projectRoot.includes('/apps/server')) {
        projectRoot = projectRoot.replace('/apps/server', '');
      }
      
      const filePath = `${projectRoot}/apps/client/dist${staticPath}`;
      const file = Bun.file(filePath);
      
      if (await file.exists()) {
        const ext = staticPath.split('.').pop()?.toLowerCase() || '';
        const mimeTypes: Record<string, string> = {
          'html': 'text/html',
          'js': 'application/javascript',
          'css': 'text/css',
          'json': 'application/json',
          'png': 'image/png',
          'jpg': 'image/jpeg',
          'svg': 'image/svg+xml',
          'ico': 'image/x-icon',
          'woff': 'font/woff',
          'woff2': 'font/woff2',
        };
        
        return new Response(file, {
          headers: {
            ...corsHeaders,
            'Content-Type': mimeTypes[ext] || 'application/octet-stream',
          }
        });
      }
      
      // SPA fallback - serve index.html for client-side routing
      const indexFile = Bun.file(`${projectRoot}/apps/client/dist/index.html`);
      if (await indexFile.exists()) {
        return new Response(indexFile, {
          headers: { ...corsHeaders, 'Content-Type': 'text/html' }
        });
      }
    }

    // ==================== DEFAULT ====================

    return new Response('buildOS Dashboard Server', {
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
    });
  },

  websocket: {
    open(ws) {
      addClient(ws);
      // Send recent events on connection
      const events = getRecentEvents(300);
      sendInitialEvents(ws, events);
    },

    message(ws: any, message: any) {
      console.log('WebSocket message:', message);
    },

    close(ws: any) {
      removeClient(ws);
    }
  }
});

console.log(`
========================================
  buildOS Dashboard Server
========================================

  HTTP:      http://localhost:${PORT}
  WebSocket: ws://localhost:${PORT}/stream

  Endpoints:
  - POST /events              - Receive events
  - GET  /events/recent       - Get recent events
  - POST /api/upload          - Upload files
  - POST /api/chat            - Trigger orchestrator
  - GET  /api/sessions        - List session logs
  - GET  /api/sessions/:id    - Get session log
  - WS   /stream              - Event stream
  
  Session Logs: .logs/conversations/
========================================
`);
