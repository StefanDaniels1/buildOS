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

import { initDatabase, getRecentEvents, getFilterOptions, insertEvent, clearEvents, getAllTools, getToolById, createTool, updateTool, deleteTool, toggleTool, getEnabledTools } from './db';
import { addClient, removeClient, sendInitialEvents, broadcastEvent } from './websocket';
import { triggerOrchestrator } from './orchestrator';
import type { HookEvent, ChatRequest, UploadedFile, CustomTool } from './types';

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

    // ==================== CUSTOM TOOLS API ====================

    // GET /api/tools - List all custom tools
    if (url.pathname === '/api/tools' && req.method === 'GET') {
      try {
        const tools = getAllTools();
        return new Response(JSON.stringify({
          success: true,
          tools
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error fetching tools:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to fetch tools'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // POST /api/tools - Create new tool
    if (url.pathname === '/api/tools' && req.method === 'POST') {
      try {
        const body = await req.json() as Partial<CustomTool>;

        // Validate required fields
        if (!body.name || !body.description || !body.handler_code) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Name, description, and handler_code are required'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Validate tool name (alphanumeric + underscore only)
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(body.name)) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Tool name must start with a letter or underscore, and contain only letters, numbers, and underscores'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        const tool: CustomTool = {
          name: body.name,
          description: body.description,
          input_schema: body.input_schema || {},
          handler_code: body.handler_code,
          enabled: body.enabled ?? true,
          env_vars: body.env_vars || {}
        };

        const created = createTool(tool);
        console.log(`Tool created: ${created.name} (id: ${created.id})`);

        return new Response(JSON.stringify({
          success: true,
          tool: created
        }), {
          status: 201,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error: any) {
        console.error('Error creating tool:', error);
        const message = error?.message?.includes('UNIQUE constraint')
          ? 'A tool with this name already exists'
          : 'Failed to create tool';
        return new Response(JSON.stringify({
          success: false,
          error: message
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /api/tools/:id - Get single tool
    if (url.pathname.match(/^\/api\/tools\/\d+$/) && req.method === 'GET') {
      try {
        const id = parseInt(url.pathname.split('/').pop()!);
        const tool = getToolById(id);

        if (!tool) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Tool not found'
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        return new Response(JSON.stringify({
          success: true,
          tool
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error fetching tool:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to fetch tool'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // PUT /api/tools/:id - Update tool
    if (url.pathname.match(/^\/api\/tools\/\d+$/) && req.method === 'PUT') {
      try {
        const id = parseInt(url.pathname.split('/').pop()!);
        const body = await req.json() as Partial<CustomTool>;

        const updated = updateTool(id, body);

        if (!updated) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Tool not found'
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        console.log(`Tool updated: ${updated.name} (id: ${id})`);

        return new Response(JSON.stringify({
          success: true,
          tool: updated
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error updating tool:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to update tool'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // DELETE /api/tools/:id - Delete tool
    if (url.pathname.match(/^\/api\/tools\/\d+$/) && req.method === 'DELETE') {
      try {
        const id = parseInt(url.pathname.split('/').pop()!);
        const deleted = deleteTool(id);

        if (!deleted) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Tool not found'
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        console.log(`Tool deleted: id ${id}`);

        return new Response(JSON.stringify({
          success: true,
          message: 'Tool deleted'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error deleting tool:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to delete tool'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // PATCH /api/tools/:id/toggle - Toggle tool enabled/disabled
    if (url.pathname.match(/^\/api\/tools\/\d+\/toggle$/) && req.method === 'PATCH') {
      try {
        const id = parseInt(url.pathname.split('/')[3]);
        const toggled = toggleTool(id);

        if (!toggled) {
          return new Response(JSON.stringify({
            success: false,
            error: 'Tool not found'
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        console.log(`Tool toggled: ${toggled.name} -> ${toggled.enabled ? 'enabled' : 'disabled'}`);

        return new Response(JSON.stringify({
          success: true,
          tool: toggled
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error toggling tool:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to toggle tool'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /api/tools/templates - Get example tool templates
    if (url.pathname === '/api/tools/templates' && req.method === 'GET') {
      const templates = [
        {
          name: 'csv_processor',
          description: 'Process CSV data from URL or context - fetch, parse, analyze, and display in spreadsheet',
          input_schema: { source: 'str', url: 'str', file_path: 'str', operation: 'str' },
          handler_code: `async def csv_processor(args: dict) -> dict:
    """
    Process CSV data from various sources.

    Args:
        source: "url", "file_path", or "inline"
        url: URL to fetch CSV from (when source="url")
        file_path: Path to CSV file (when source="file_path")
        operation: "parse", "analyze", or "display"

    Returns:
        Processed CSV data ready for spreadsheet display
    """
    import csv
    import io
    from collections import Counter

    source = args.get("source", "file_path")
    operation = args.get("operation", "display")

    # Get CSV content
    csv_content = ""
    if source == "url":
        import httpx
        url = args.get("url")
        if not url:
            return {"success": False, "error": "url is required"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            csv_content = response.text
    elif source == "file_path":
        file_path = args.get("file_path")
        if not file_path:
            return {"success": False, "error": "file_path is required"}
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            csv_content = f.read()
    else:
        return {"success": False, "error": f"Invalid source: {source}"}

    # Parse CSV
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    if not rows:
        return {"success": False, "error": "CSV is empty"}

    headers = rows[0]
    data_rows = rows[1:]

    if operation == "analyze":
        # Analyze columns
        analysis = []
        for i, header in enumerate(headers):
            values = [row[i] if i < len(row) else "" for row in data_rows]
            non_empty = [v for v in values if v.strip()]
            analysis.append({
                "column": header,
                "total": len(values),
                "non_empty": len(non_empty),
                "unique": len(set(non_empty)),
                "top_values": [{"value": v, "count": c} for v, c in Counter(non_empty).most_common(5)]
            })
        return {"success": True, "analysis": analysis, "row_count": len(data_rows)}

    # Default: display in spreadsheet format
    columns = [{"title": h, "width": 120} for h in headers]

    return {
        "success": True,
        "spreadsheet": {
            "type": "spreadsheet",
            "name": "CSV Data",
            "data": rows,
            "columns": columns,
            "row_count": len(rows),
            "column_count": len(columns)
        },
        "message": "Switch to Spreadsheet view to see data"
    }`,
          env_vars: {}
        },
        {
          name: 'http_request',
          description: 'Make HTTP requests to any API',
          input_schema: { url: 'str', method: 'str', headers: 'dict', body: 'dict' },
          handler_code: `async def http_request(args: dict) -> dict:
    """Make an HTTP request to an API endpoint."""
    import httpx

    url = args.get("url")
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    body = args.get("body")

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=body if body else None
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }`,
          env_vars: {}
        },
        {
          name: 'autodesk_aps_projects',
          description: 'Get projects from Autodesk APS (Forge)',
          input_schema: { hub_id: 'str', limit: 'int' },
          handler_code: `async def autodesk_aps_projects(args: dict) -> dict:
    """Fetch projects from Autodesk APS (Platform Services)."""
    import httpx
    import os
    import time

    hub_id = args.get("hub_id")
    limit = args.get("limit", 50)

    if not hub_id:
        return {"success": False, "error": "hub_id is required"}

    client_id = os.environ.get("APS_CLIENT_ID")
    client_secret = os.environ.get("APS_CLIENT_SECRET")

    if not client_id or not client_secret:
        return {"success": False, "error": "APS_CLIENT_ID and APS_CLIENT_SECRET must be set"}

    # Get access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://developer.api.autodesk.com/authentication/v2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "data:read"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        # Get projects
        projects_response = await client.get(
            f"https://developer.api.autodesk.com/project/v1/hubs/{hub_id}/projects",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"page[limit]": limit}
        )

        data = projects_response.json()
        projects = [
            {
                "id": item["id"],
                "name": item["attributes"]["name"],
                "created_at": item["attributes"].get("createdTime")
            }
            for item in data.get("data", [])
        ]

        return {"success": True, "hub_id": hub_id, "project_count": len(projects), "projects": projects}`,
          env_vars: { APS_CLIENT_ID: '', APS_CLIENT_SECRET: '' }
        }
      ];

      return new Response(JSON.stringify({
        success: true,
        templates
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // ==================== SPREADSHEET API ====================

    // POST /api/spreadsheet/save - Save spreadsheet data to session context
    if (url.pathname === '/api/spreadsheet/save' && req.method === 'POST') {
      try {
        const body = await req.json();
        const { session_id, spreadsheet } = body;

        if (!session_id || !spreadsheet) {
          return new Response(JSON.stringify({
            success: false,
            error: 'session_id and spreadsheet are required'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Find workspace directory
        let workspaceDir = process.cwd();
        if (workspaceDir.includes('/apps/server')) {
          workspaceDir = workspaceDir.replace('/apps/server', '') + '/workspace';
        } else if (workspaceDir.includes('/apps')) {
          workspaceDir = workspaceDir.replace('/apps', '') + '/workspace';
        } else {
          workspaceDir = workspaceDir + '/workspace';
        }

        // Extract user_id from session_id if present, or use a shared folder
        // Session format: session_timestamp_random or just session_xxx
        const sessionPart = session_id.split('_').slice(1, 3).join('_');
        const spreadsheetDir = `${workspaceDir}/.context/spreadsheets`;

        // Ensure directory exists
        await Bun.write(`${spreadsheetDir}/.gitkeep`, '');

        // Save spreadsheet as JSON
        const filename = `${session_id}_${spreadsheet.name?.replace(/[^a-zA-Z0-9_-]/g, '_') || 'spreadsheet'}.json`;
        const filepath = `${spreadsheetDir}/${filename}`;

        await Bun.write(filepath, JSON.stringify({
          ...spreadsheet,
          session_id,
          saved_at: new Date().toISOString()
        }, null, 2));

        console.log(`Spreadsheet saved: ${filepath}`);

        return new Response(JSON.stringify({
          success: true,
          filepath: filepath,
          message: 'Spreadsheet saved successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error saving spreadsheet:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to save spreadsheet'
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /api/spreadsheet/load - Load spreadsheet data for a session
    if (url.pathname === '/api/spreadsheet/load' && req.method === 'GET') {
      try {
        const session_id = url.searchParams.get('session_id');

        if (!session_id) {
          return new Response(JSON.stringify({
            success: false,
            error: 'session_id is required'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Find workspace directory
        let workspaceDir = process.cwd();
        if (workspaceDir.includes('/apps/server')) {
          workspaceDir = workspaceDir.replace('/apps/server', '') + '/workspace';
        } else if (workspaceDir.includes('/apps')) {
          workspaceDir = workspaceDir.replace('/apps', '') + '/workspace';
        } else {
          workspaceDir = workspaceDir + '/workspace';
        }

        const spreadsheetDir = `${workspaceDir}/.context/spreadsheets`;

        // Find spreadsheet files for this session
        const proc = Bun.spawn(['ls', spreadsheetDir], { stdout: 'pipe', stderr: 'pipe' });
        const output = await new Response(proc.stdout).text();
        const files = output.split('\n').filter(f => f.startsWith(session_id) && f.endsWith('.json'));

        if (files.length === 0) {
          return new Response(JSON.stringify({
            success: true,
            spreadsheets: []
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Load all spreadsheets for this session
        const spreadsheets = [];
        for (const filename of files) {
          const filepath = `${spreadsheetDir}/${filename}`;
          const file = Bun.file(filepath);
          if (await file.exists()) {
            const content = await file.json();
            spreadsheets.push(content);
          }
        }

        return new Response(JSON.stringify({
          success: true,
          spreadsheets
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error loading spreadsheets:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to load spreadsheets'
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
