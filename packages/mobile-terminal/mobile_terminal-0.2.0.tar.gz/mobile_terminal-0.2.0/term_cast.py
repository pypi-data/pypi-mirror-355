#!/usr/bin/env python3
"""
mobile-terminal: The terminal moves with you
Access and control your terminal from any mobile device
"""

__version__ = "0.2.0"

import os
import sys
import pty
import asyncio
import json
import socket
import subprocess
import platform
import signal
import time
import struct
import termios
import fcntl
from pathlib import Path
import logging

try:
    from aiohttp import web
    import aiofiles
except ImportError:
    print("Please install dependencies: pip install aiohttp aiofiles")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TerminalBroadcaster:
    def __init__(self, port=8080):
        self.port = port
        self.clients = set()
        self.pty_master = None
        self.pty_slave = None
        self.process = None
        self.buffer = []
        self.max_buffer_size = 10000  # Keep last 10k lines
        self.waiting_for_input = False
        self.last_output_time = time.time()
        self.sleep_preventer = None
        
    def start_pty(self, command):
        """Start a pseudo-terminal with the given command"""
        try:
            self.pty_master, self.pty_slave = pty.openpty()
            
            # Set terminal size
            # Set a reasonable terminal size (rows=24, cols=80)
            size = struct.pack('HHHH', 24, 80, 0, 0)
            fcntl.ioctl(self.pty_slave, termios.TIOCSWINSZ, size)
            
            # Make PTY non-blocking
            flags = fcntl.fcntl(self.pty_master, fcntl.F_GETFL)
            fcntl.fcntl(self.pty_master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            # Set environment for interactive shell
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['PS1'] = '$ '  # Simple prompt
            
            # For interactive shells, add -i flag
            if command in ['/bin/bash', '/bin/zsh', '/bin/sh'] or command.endswith('bash') or command.endswith('zsh'):
                command = f"{command} -i"
            
            # Start the process
            self.process = subprocess.Popen(
                command,
                stdin=self.pty_slave,
                stdout=self.pty_slave,
                stderr=self.pty_slave,
                shell=True,
                env=env,
                preexec_fn=os.setsid  # Create new session
            )
            
            # Close the slave FD in parent process
            os.close(self.pty_slave)
            self.pty_slave = None
            
            logger.info(f"Started process with PID: {self.process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start PTY: {e}")
            raise
        
    async def read_pty_output(self):
        """Read output from PTY and broadcast to clients"""
        while self.process and self.process.poll() is None:
            try:
                # Try to read from PTY
                try:
                    output = os.read(self.pty_master, 4096).decode('utf-8', errors='replace')
                    
                    if output:
                        logger.debug(f"PTY output: {repr(output)}")
                        self.last_output_time = time.time()
                        self.buffer.append(output)
                        
                        # Trim buffer if too large
                        if len(self.buffer) > self.max_buffer_size:
                            self.buffer = self.buffer[-self.max_buffer_size:]
                        
                        # Check if waiting for input
                        is_prompt = self.detect_prompt(output)
                        
                        await self.broadcast({
                            'type': 'prompt' if is_prompt else 'output',
                            'data': output,
                            'timestamp': time.time(),
                            'needs_input': is_prompt
                        })
                        
                except BlockingIOError:
                    # No data available, wait a bit
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error reading PTY: {e}")
                break
                
        # Process ended
        await self.broadcast({
            'type': 'exit',
            'code': self.process.returncode if self.process else -1
        })
        
    def detect_prompt(self, output):
        """Detect if terminal is waiting for input"""
        # Common prompt patterns
        prompt_patterns = [
            '[Y/n]', '[y/N]', '(y/n)', '(yes/no)',
            'password:', 'Password:', 'passphrase:',
            'Continue?', 'Proceed?', 'OK?',
            'Enter', 'Input', 'Type',
            'Press any key', 'Hit enter'
        ]
        
        output_lower = output.lower().strip()
        
        # Check for common patterns
        for pattern in prompt_patterns:
            if pattern.lower() in output_lower:
                return True
                
        # Check if line ends with common prompt characters
        if output.rstrip().endswith((':', '?', '>', '$', '#', ']')):
            # Additional heuristic: if no output for a bit, probably waiting
            if time.time() - self.last_output_time > 0.5:
                return True
                
        return False
        
    async def broadcast(self, message):
        """Send message to all connected clients"""
        if self.clients:
            message_str = json.dumps(message)
            disconnected = set()
            
            for client in self.clients:
                try:
                    await client.send_str(message_str)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.add(client)
                    
            # Remove disconnected clients
            self.clients -= disconnected
            
    def send_input(self, data):
        """Send input to the PTY"""
        if self.pty_master:
            try:
                # Send the input
                bytes_written = os.write(self.pty_master, data.encode('utf-8'))
                logger.info(f"Sent input: {repr(data)} ({bytes_written} bytes)")
            except Exception as e:
                logger.error(f"Failed to send input: {e}")

class SleepPreventer:
    """Prevent system sleep while broadcasting"""
    
    def __init__(self):
        self.system = platform.system()
        self.process = None
        
    def start(self):
        """Start preventing sleep"""
        try:
            if self.system == 'Darwin':  # macOS
                self.process = subprocess.Popen(
                    ['caffeinate', '-d', '-i', '-s'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("Sleep prevention started (macOS)")
            elif self.system == 'Linux':
                # Try systemd-inhibit first
                try:
                    self.process = subprocess.Popen([
                        'systemd-inhibit',
                        '--what=idle:sleep:shutdown',
                        '--who=mobile-terminal',
                        '--why=Terminal broadcast active',
                        'cat'
                    ], stdin=subprocess.PIPE)
                    logger.info("Sleep prevention started (Linux systemd)")
                except:
                    logger.warning("systemd-inhibit not available")
            elif self.system == 'Windows':
                # Windows SetThreadExecutionState
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ES_SYSTEM_REQUIRED = 0x00000001
                ES_DISPLAY_REQUIRED = 0x00000002
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                )
                logger.info("Sleep prevention started (Windows)")
        except Exception as e:
            logger.warning(f"Could not prevent sleep: {e}")
            
    def stop(self):
        """Stop preventing sleep"""
        if self.process:
            self.process.terminate()
            self.process = None

# Global broadcaster instance
broadcaster = None

async def handle_websocket(request):
    """Handle WebSocket connections from phones"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    if not broadcaster:
        logger.error("Broadcaster not initialized")
        return ws
    
    broadcaster.clients.add(ws)
    logger.info(f"Client connected. Total clients: {len(broadcaster.clients)}")
    
    try:
        # Send welcome message
        await ws.send_str(json.dumps({
            'type': 'welcome',
            'data': 'Connected to mobile-terminal'
        }))
        
        # Send buffer to new client
        if broadcaster.buffer:
            recent_output = ''.join(broadcaster.buffer[-50:])
            if recent_output.strip():
                await ws.send_str(json.dumps({
                    'type': 'history',
                    'data': recent_output
                }))
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data['type'] == 'input':
                        broadcaster.send_input(data['data'])
                    elif data['type'] == 'ping':
                        await ws.send_str(json.dumps({'type': 'pong'}))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {msg.data}")
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        try:
            broadcaster.clients.remove(ws)
        except KeyError:
            pass
        logger.info(f"Client disconnected. Total clients: {len(broadcaster.clients)}")
        
    return ws

async def handle_index(request):
    """Serve the web UI"""
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=3, user-scalable=yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>mobile-terminal</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Consolas', monospace;
            background: #0d1117;
            color: #c9d1d9;
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
            font-size: 14px;
            line-height: 1.5;
        }
        
        #terminal {
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
            padding: 12px;
            background: #0d1117;
            white-space: pre;
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
            font-size: 14px;
            /* Better readability on mobile */
            letter-spacing: 0.5px;
            /* Prevent text selection issues */
            -webkit-user-select: text;
            user-select: text;
        }
        
        /* Landscape mode - smaller font */
        @media (orientation: landscape) {
            body { font-size: 12px; }
            #terminal { font-size: 12px; }
        }
        
        /* Tablet and larger */
        @media (min-width: 768px) {
            body { font-size: 16px; }
            #terminal { 
                font-size: 16px;
                padding: 20px;
            }
        }
        
        /* Custom scrollbar for webkit */
        #terminal::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        #terminal::-webkit-scrollbar-track {
            background: #1e1e1e;
        }
        
        #terminal::-webkit-scrollbar-thumb {
            background: #484f58;
            border-radius: 4px;
        }
        
        #terminal::-webkit-scrollbar-corner {
            background: #1e1e1e;
        }
        
        #status {
            padding: 8px 12px;
            background: #161b22;
            color: #c9d1d9;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
            flex-shrink: 0;
        }
        
        #status.connected {
            border-bottom-color: #238636;
        }
        
        #status.disconnected {
            background: #da3633;
            color: white;
        }
        
        #input-area {
            background: #2d2d2d;
            padding: 10px;
            border-top: 1px solid #444;
            display: none;
        }
        
        #input-area.active {
            display: block;
        }
        
        #input-area.interactive {
            display: block;
            background: #1a1a1a;
        }
        
        .mode-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #007ACC;
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }
        
        .mode-toggle.interactive {
            background: #0dbc79;
        }
        
        #command-input {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            font-family: inherit;
            background: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #444;
            border-radius: 4px;
            outline: none;
        }
        
        #command-input:focus {
            border-color: #007ACC;
        }
        
        .quick-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        
        .quick-button {
            padding: 10px 20px;
            background: #0e639c;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            font-family: inherit;
            touch-action: manipulation;
        }
        
        .quick-button:active {
            background: #1177bb;
        }
        
        .alert {
            background: #f4b643;
            color: #000;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        /* Better ANSI colors for mobile readability */
        .ansi-black { color: #484f58; }
        .ansi-red { color: #ff7b72; }
        .ansi-green { color: #3fb950; }
        .ansi-yellow { color: #d29922; }
        .ansi-blue { color: #58a6ff; }
        .ansi-magenta { color: #bc8cff; }
        .ansi-cyan { color: #39c5cf; }
        .ansi-white { color: #b1bac4; }
        
        .ansi-bright-black { color: #6e7681; }
        .ansi-bright-red { color: #ffa198; }
        .ansi-bright-green { color: #56d364; }
        .ansi-bright-yellow { color: #e3b341; }
        .ansi-bright-blue { color: #79c0ff; }
        .ansi-bright-magenta { color: #d2a8ff; }
        .ansi-bright-cyan { color: #56d4dd; }
        .ansi-bright-white { color: #f0f6fc; }
        
        /* Zoom controls */
        .zoom-controls {
            position: fixed;
            top: 50px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 100;
        }
        
        .zoom-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0.7;
        }
        
        .zoom-btn:active {
            background: #30363d;
        }
        
        /* Line numbers for better tracking */
        .line-number {
            color: #484f58;
            user-select: none;
            padding-right: 10px;
            display: inline-block;
            width: 40px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div id="status">
        <span id="status-text">Connecting...</span>
        <span id="connection-info"></span>
    </div>
    
    <div id="terminal"></div>
    
    <div class="zoom-controls">
        <button class="zoom-btn" onclick="adjustFontSize(1)">+</button>
        <button class="zoom-btn" onclick="adjustFontSize(-1)">−</button>
        <button class="zoom-btn" onclick="resetFontSize()">↺</button>
    </div>
    
    <div id="input-area">
        <div class="alert" id="input-alert" style="display: none;">
            ⚠️ Input Required
        </div>
        <input type="text" id="command-input" placeholder="Type response..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
        <div class="quick-buttons">
            <button class="quick-button" onclick="sendInput('y\\\\n')">Yes (y)</button>
            <button class="quick-button" onclick="sendInput('n\\\\n')">No (n)</button>
            <button class="quick-button" onclick="sendInput('\\\\n')">Enter ↵</button>
            <button class="quick-button" onclick="sendInput('\\\\x03')">Ctrl+C</button>
            <button class="quick-button" onclick="sendInput('\\\\x04')">Ctrl+D</button>
            <button class="quick-button" onclick="sendInput('\\\\x1a')">Ctrl+Z</button>
        </div>
    </div>
    
    <button class="mode-toggle" id="mode-toggle" onclick="toggleInteractiveMode()">⌨️</button>

    <script>
        // Ignore Chrome extension errors
        window.addEventListener('error', function(e) {
            if (e.filename && e.filename.includes('chrome-extension://')) {
                e.preventDefault();
                return true;
            }
        });
        
        const terminal = document.getElementById('terminal');
        const statusEl = document.getElementById('status');
        const statusText = document.getElementById('status-text');
        const inputArea = document.getElementById('input-area');
        const inputAlert = document.getElementById('input-alert');
        const commandInput = document.getElementById('command-input');
        
        let ws = null;
        let reconnectTimeout = null;
        let isConnected = false;
        let interactiveMode = false;
        let currentFontSize = 14;
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Keep screen awake
        let wakeLock = null;
        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    console.log('Wake lock active');
                }
            } catch (err) {
                console.log('Wake lock failed:', err);
            }
        }
        
        // Font size controls
        function adjustFontSize(delta) {
            currentFontSize = Math.max(10, Math.min(24, currentFontSize + delta));
            terminal.style.fontSize = currentFontSize + 'px';
            document.body.style.fontSize = currentFontSize + 'px';
            localStorage.setItem('termcastFontSize', currentFontSize);
        }
        
        function resetFontSize() {
            currentFontSize = 14;
            terminal.style.fontSize = currentFontSize + 'px';
            document.body.style.fontSize = currentFontSize + 'px';
            localStorage.removeItem('termcastFontSize');
        }
        
        // Load saved font size
        const savedFontSize = localStorage.getItem('termcastFontSize');
        if (savedFontSize) {
            currentFontSize = parseInt(savedFontSize);
            terminal.style.fontSize = currentFontSize + 'px';
            document.body.style.fontSize = currentFontSize + 'px';
        }
        
        // Terminal screen buffer for handling cursor movements
        let screenBuffer = [];
        let cursorY = 0;
        let maxLines = 1000;
        
        // Process ANSI escape sequences and cursor movements
        function processTerminalOutput(text) {
            let i = 0;
            
            while (i < text.length) {
                // Check for ANSI escape sequence
                if (text[i] === '\\x1b' && text[i + 1] === '[') {
                    let j = i + 2;
                    let params = '';
                    
                    // Read parameters
                    while (j < text.length && /[0-9;]/.test(text[j])) {
                        params += text[j];
                        j++;
                    }
                    
                    if (j < text.length) {
                        const code = text[j];
                        const paramArray = params.split(';').map(p => parseInt(p) || 1);
                        
                        switch (code) {
                            case 'A': // Cursor up
                                cursorY = Math.max(0, cursorY - paramArray[0]);
                                break;
                            case 'K': // Clear line
                                if (screenBuffer[cursorY]) {
                                    screenBuffer[cursorY] = '';
                                }
                                break;
                            case 'J': // Clear screen
                                if (paramArray[0] === 2 || paramArray[0] === 3) {
                                    screenBuffer = [];
                                    cursorY = 0;
                                }
                                break;
                            case 'H': // Cursor home
                                cursorY = 0;
                                break;
                        }
                        i = j + 1;
                        continue;
                    }
                }
                
                // Handle special characters
                if (text[i] === '\\r') {
                    // Carriage return - stay on same line
                    i++;
                    continue;
                } else if (text[i] === '\\n') {
                    // Newline - move to next line
                    cursorY++;
                    i++;
                    continue;
                } else if (text.charCodeAt(i) === 8) {
                    // Backspace
                    if (screenBuffer[cursorY] && screenBuffer[cursorY].length > 0) {
                        screenBuffer[cursorY] = screenBuffer[cursorY].slice(0, -1);
                    }
                    i++;
                    continue;
                }
                
                // Regular character
                if (text.charCodeAt(i) >= 32 || text.charCodeAt(i) === 9) {
                    if (!screenBuffer[cursorY]) {
                        screenBuffer[cursorY] = '';
                    }
                    screenBuffer[cursorY] += text[i];
                }
                i++;
            }
            
            // Trim buffer if too large
            if (screenBuffer.length > maxLines) {
                screenBuffer = screenBuffer.slice(-maxLines);
                cursorY = Math.min(cursorY, screenBuffer.length - 1);
            }
            
            return screenBuffer.filter(line => line !== undefined).join('\\n');
        }
        
        // Clean text output - remove remaining ANSI codes
        function cleanText(text) {
            // Remove any remaining ANSI codes
            return text.replace(/\\x1b\\[[0-9;]*[A-Za-z]/g, '')
                      .replace(/\\[\\?2004[hl]/g, '');
        }
        
        function connect() {
            statusText.textContent = '⟳ Connecting...';
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            console.log('Connecting to:', wsUrl);
            
            try {
                ws = new WebSocket(wsUrl);
            } catch (e) {
                console.error('WebSocket creation failed:', e);
                statusText.textContent = '❌ Failed to create connection';
                return;
            }
            
            // Add connection timeout
            const connectionTimeout = setTimeout(() => {
                if (ws.readyState !== WebSocket.OPEN) {
                    console.error('Connection timeout');
                    statusText.textContent = '⏱️ Connection timeout';
                    ws.close();
                }
            }, 5000);
            
            ws.onopen = () => {
                clearTimeout(connectionTimeout);
                isConnected = true;
                statusEl.classList.remove('disconnected');
                statusEl.classList.add('connected');
                statusText.textContent = '● Connected';
                console.log('WebSocket connected');
                requestWakeLock();
                
                // Send ping every 30s to keep connection alive
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            };
            
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                
                switch (msg.type) {
                    case 'output':
                        appendOutput(msg.data);
                        break;
                        
                    case 'prompt':
                        appendOutput(msg.data);
                        showInputArea();
                        
                        // Vibrate phone
                        if ('vibrate' in navigator) {
                            navigator.vibrate([200, 100, 200]);
                        }
                        
                        // Show notification
                        if ('Notification' in window && Notification.permission === 'granted') {
                            new Notification('Terminal needs input', {
                                body: msg.data.trim().split('\\n').pop(),
                                icon: '/icon.png',
                                requireInteraction: true
                            });
                        }
                        break;
                        
                    case 'history':
                        terminal.innerHTML = '';
                        appendOutput(msg.data);
                        break;
                        
                    case 'exit':
                        appendOutput(`\\n\\n[Process exited with code ${msg.code}]`);
                        hideInputArea();
                        isInteractiveMode = false;
                        screenBuffer = [];
                        cursorY = 0;
                        break;
                }
            };
            
            ws.onclose = (event) => {
                isConnected = false;
                statusEl.classList.add('disconnected');
                statusEl.classList.remove('connected');
                statusText.textContent = '○ Disconnected - Reconnecting...';
                console.log('WebSocket closed:', event.code, event.reason);
                
                // Try to reconnect after 2 seconds
                clearTimeout(reconnectTimeout);
                reconnectTimeout = setTimeout(connect, 2000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                statusText.textContent = '⚠️ Connection error';
            };
        }
        
        let isInteractiveMode = false;
        
        function appendOutput(text) {
            // Detect if this is an interactive application (lots of cursor movements)
            if (text.includes('\\x1b[1A') || text.includes('\\x1b[2K')) {
                isInteractiveMode = true;
            }
            
            if (isInteractiveMode) {
                // Use terminal emulation for interactive apps
                const processed = processTerminalOutput(text);
                terminal.textContent = processed;
                // Update status to show interactive mode
                document.getElementById('connection-info').textContent = window.location.host + ' (Interactive)';
            } else {
                // Regular output mode
                // First handle backspaces
                let processed = '';
                for (let i = 0; i < text.length; i++) {
                    if (text.charCodeAt(i) === 8) { // Backspace
                        processed = processed.slice(0, -1);
                    } else {
                        processed += text[i];
                    }
                }
                
                const escaped = processed
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\\r\\n/g, '\\n')
                    .replace(/\\r/g, '\\n');
                
                const cleaned = cleanText(escaped);
                
                // Append to terminal
                const lines = cleaned.split('\\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        const div = document.createElement('div');
                        div.textContent = line;
                        terminal.appendChild(div);
                    }
                });
            }
            
            // Smart scrolling - only if user is near bottom
            const isNearBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 100;
            if (isNearBottom) {
                terminal.scrollTop = terminal.scrollHeight;
            }
            
            // Trim if too long (keep last 1000 divs)
            while (terminal.children.length > 1000) {
                terminal.removeChild(terminal.firstChild);
            }
        }
        
        function showInputArea() {
            if (!interactiveMode) {
                inputArea.classList.add('active');
                inputAlert.style.display = 'block';
            }
            commandInput.focus();
        }
        
        function hideInputArea() {
            if (!interactiveMode) {
                inputArea.classList.remove('active');
                inputAlert.style.display = 'none';
            }
            commandInput.value = '';
        }
        
        function toggleInteractiveMode() {
            interactiveMode = !interactiveMode;
            const toggle = document.getElementById('mode-toggle');
            
            if (interactiveMode) {
                inputArea.classList.add('interactive');
                inputArea.classList.remove('active');
                inputAlert.style.display = 'none';
                toggle.classList.add('interactive');
                toggle.innerHTML = '💬';
                commandInput.placeholder = 'Type command and press Enter...';
                commandInput.focus();
            } else {
                inputArea.classList.remove('interactive');
                toggle.classList.remove('interactive');
                toggle.innerHTML = '⌨️';
                commandInput.placeholder = 'Type response...';
            }
        }
        
        function sendInput(text) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Replace escape sequences with actual characters
                const actualText = text
                    .replace(/\\\\n/g, '\\n')
                    .replace(/\\\\r/g, '\\r')
                    .replace(/\\\\t/g, '\\t')
                    .replace(/\\\\x03/g, String.fromCharCode(3))
                    .replace(/\\\\x04/g, String.fromCharCode(4))
                    .replace(/\\\\x1a/g, String.fromCharCode(26));
                
                ws.send(JSON.stringify({
                    type: 'input',
                    data: actualText
                }));
                hideInputArea();
            }
        }
        
        // Input handling
        commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendInput(commandInput.value + '\\n');
            }
        });
        
        // Prevent zooming on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Debug info
        console.log('mobile-terminal UI loaded');
        console.log('Current location:', window.location.host);
        
        // Show connection info
        document.getElementById('connection-info').textContent = window.location.host;
        
        // Start connection with small delay to ensure DOM is ready
        setTimeout(() => {
            console.log('Starting WebSocket connection...');
            connect();
        }, 100);
    </script>
</body>
</html>'''
    
    return web.Response(text=html, content_type='text/html')

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

async def main(command, port=8080, host='0.0.0.0'):
    """Main entry point"""
    global broadcaster
    
    logger.info(f"Starting term-cast server on {host}:{port}")
    logger.info(f"Command: {command}")
    
    # Create broadcaster
    broadcaster = TerminalBroadcaster(port)
    
    # Start sleep prevention
    sleep_preventer = SleepPreventer()
    sleep_preventer.start()
    broadcaster.sleep_preventer = sleep_preventer
    
    # Start PTY with command
    try:
        broadcaster.start_pty(command)
    except Exception as e:
        logger.error(f"Failed to start command '{command}': {e}")
        return
    
    # Create web app
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', handle_websocket)
    
    # Get local IP
    local_ip = get_local_ip()
    
    print(f"\n{'='*60}")
    print(f"📱 mobile-terminal is running!")
    print(f"{'='*60}")
    print(f"\n🌐 URLs:")
    print(f"  Mobile: http://{local_ip}:{port}")
    print(f"  Local:  http://localhost:{port}")
    print(f"\n💻 Command: {command}")
    print(f"📡 Server: {host}:{port}")
    print(f"\n💡 Tips:")
    print(f"  - Ensure phone is on same WiFi network")
    print(f"  - Tap ⌨️ button for interactive mode")
    print(f"  - Use +/- buttons to adjust font size")
    print(f"  - For internet access: ngrok http {port}")
    print(f"\nPress Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        raise KeyboardInterrupt()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run web server
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Web server started on {host}:{port}")
        
        # Start PTY reader AFTER server is running
        asyncio.create_task(broadcaster.read_pty_output())
        logger.info("PTY reader started")
        
        # Keep running until process ends or interrupted
        while broadcaster.process and broadcaster.process.poll() is None:
            await asyncio.sleep(1)
            
    except OSError as e:
        logger.error(f"Failed to start server on {host}:{port}: {e}")
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print(f"Try a different port: python term_cast.py --port 8081")
        return
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if broadcaster and broadcaster.process:
            broadcaster.process.terminate()
        if sleep_preventer:
            sleep_preventer.stop()
        logger.info("Shutdown complete")

def main_cli():
    """CLI entry point for setup.py"""
    import argparse
    
    parser = argparse.ArgumentParser(description='mobile-terminal: The terminal moves with you')
    parser.add_argument('command', nargs='*', help='Command to run (default: interactive shell)')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to serve on (default: 8080)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine command
    if args.command:
        command = ' '.join(args.command)
    else:
        command = os.environ.get('SHELL', '/bin/bash')
    
    try:
        asyncio.run(main(command, args.port, args.host))
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main_cli()