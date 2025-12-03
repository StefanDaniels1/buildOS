/**
 * buildOS Orchestrator Integration
 *
 * Spawns orchestrator.py as subprocess and streams output back to dashboard.
 */

import { broadcastEvent } from './websocket';
import type { HookEvent } from './types';

/**
 * Trigger the buildOS orchestrator with a user message.
 *
 * @param message - User's natural language request
 * @param sessionId - Unique session identifier
 * @param filePath - Optional path to uploaded file
 * @param availableFiles - Optional list of all available file paths
 * @param apiKey - Anthropic API key (from user or environment)
 */
export async function triggerOrchestrator(
  message: string,
  sessionId: string,
  filePath?: string,
  availableFiles?: string[],
  apiKey?: string
): Promise<void> {
  console.log(`[Orchestrator] ========== STARTING ==========`);
  console.log(`[Orchestrator] Session: ${sessionId}`);
  console.log(`[Orchestrator] Message: ${message}`);
  console.log(`[Orchestrator] filePath param:`, filePath);
  console.log(`[Orchestrator] availableFiles param:`, availableFiles);
  console.log(`[Orchestrator] availableFiles length:`, availableFiles?.length || 0);

  // Send initial user prompt event
  broadcastEvent({
    source_app: 'buildos-orchestrator',
    session_id: sessionId,
    hook_event_type: 'UserPromptSubmit',
    payload: {
      prompt: message,
      filePath: filePath || null,
      availableFiles: availableFiles || [],
      timestamp: Date.now()
    }
  });

  try {
    // Use process.cwd() as base and work upward to find agent_system5
    let projectRoot = process.cwd();
    
    // If we're in apps/server, navigate to root
    if (projectRoot.includes('/apps/server')) {
      projectRoot = projectRoot.replace('/apps/server', '');
    } else if (projectRoot.includes('/apps')) {
      projectRoot = projectRoot.replace('/apps', '');
    }
    
    const orchestratorPath = `${projectRoot}/orchestrator.py`;

    console.log(`[Orchestrator] Script: ${orchestratorPath}`);
    console.log(`[Orchestrator] CWD: ${projectRoot}`);
    console.log(`[Orchestrator] process.cwd(): ${process.cwd()}`);

    const args = [
      'python3',
      orchestratorPath,
      '--message', message,
      '--session-id', sessionId,
      '--dashboard-url', `http://localhost:${process.env.SERVER_PORT || 4000}`
    ];

    // Add file path if provided
    if (filePath) {
      const absoluteFilePath = filePath.startsWith('/')
        ? filePath
        : `${projectRoot}/${filePath}`;
      args.push('--file-path', absoluteFilePath);
      console.log(`[Orchestrator] Resolved file: ${absoluteFilePath}`);
    }
    
    // Add available files if provided
    if (availableFiles && availableFiles.length > 0) {
      const absoluteAvailableFiles = availableFiles.map(f => 
        f.startsWith('/') ? f : `${projectRoot}/${f}`
      );
      args.push('--available-files', JSON.stringify(absoluteAvailableFiles));
      console.log(`[Orchestrator] Added --available-files with ${absoluteAvailableFiles.length} files`);
    } else {
      console.log(`[Orchestrator] NO available files to add (availableFiles=${JSON.stringify(availableFiles)})`);
    }

    console.log(`[Orchestrator] Full args:`, args.join(' '));

    const proc = Bun.spawn(args, {
      cwd: projectRoot,
      env: {
        ...process.env,
        BUILDOS_SESSION_ID: sessionId,
        PYTHONPATH: projectRoot,
        // Pass API key to orchestrator (user-provided or from environment)
        ANTHROPIC_API_KEY: apiKey || process.env.ANTHROPIC_API_KEY || ''
      },
      stdout: 'pipe',
      stderr: 'pipe'
    });

    // Stream stdout
    const decoder = new TextDecoder();
    (async () => {
      for await (const chunk of proc.stdout) {
        const text = decoder.decode(chunk).trim();
        if (text) {
          console.log(`[Orchestrator stdout] ${text}`);
        }
      }
    })();

    // Capture stderr
    let stderrOutput = '';
    (async () => {
      for await (const chunk of proc.stderr) {
        const text = decoder.decode(chunk);
        stderrOutput += text;
        // Only log non-debug stderr
        if (!text.includes('DEBUG') && !text.includes('INFO')) {
          console.error(`[Orchestrator stderr] ${text}`);
        }
      }
    })();

    // Wait for process to complete
    await proc.exited;

    if (proc.exitCode !== 0) {
      const errorMsg = stderrOutput || `Orchestrator exited with code ${proc.exitCode}`;
      console.error(`[Orchestrator] Error: ${errorMsg}`);

      broadcastEvent({
        source_app: 'buildos-orchestrator',
        session_id: sessionId,
        hook_event_type: 'Stop',
        payload: {
          status: 'error',
          message: errorMsg.slice(0, 500),
          timestamp: Date.now()
        }
      });
    }

  } catch (error) {
    console.error('[Orchestrator] Error:', error);

    broadcastEvent({
      source_app: 'buildos-orchestrator',
      session_id: sessionId,
      hook_event_type: 'Stop',
      payload: {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      }
    });
  }
}
