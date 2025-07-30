# term-cast Technical Documentation

## Overview

term-cast is a real-time terminal broadcasting tool that captures terminal output and streams it to web browsers via WebSocket connections. It creates a bridge between traditional command-line interfaces and modern web technologies.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Terminal      │────▶│  term-cast   │────▶│  Web Browser    │
│   (PTY)         │     │  (Python)    │     │  (WebSocket)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                      │                      │
        │                      │                      │
    Command I/O          Capture/Process         Display/Input
```

## Core Components

### 1. Pseudo-Terminal (PTY) Management

term-cast uses Python's `pty` module to create a pseudo-terminal that acts as an intermediary between the actual terminal and the broadcasting system.

```python
# PTY creation
self.pty_master, self.pty_slave = pty.openpty()

# Terminal configuration
size = struct.pack('HHHH', 24, 80, 0, 0)  # rows, cols, xpixel, ypixel
fcntl.ioctl(self.pty_slave, termios.TIOCSWINSZ, size)

# Non-blocking I/O
flags = fcntl.fcntl(self.pty_master, fcntl.F_GETFL)
fcntl.fcntl(self.pty_master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
```

**Why PTY?**
- Provides full terminal emulation including control sequences
- Captures both input and output streams
- Preserves terminal behaviors (colors, cursor movement, etc.)
- Allows bidirectional communication

### 2. Process Management

The target command/shell runs as a subprocess connected to the PTY:

```python
self.process = subprocess.Popen(
    command,
    stdin=self.pty_slave,
    stdout=self.pty_slave,
    stderr=self.pty_slave,
    shell=True,
    env=env,
    preexec_fn=os.setsid  # Create new session
)
```

**Key aspects:**
- `preexec_fn=os.setsid`: Creates a new session, preventing signal propagation issues
- All streams (stdin/stdout/stderr) connected to PTY slave
- Environment variables passed through with TERM=xterm-256color

### 3. Asynchronous I/O Loop

The core read loop continuously monitors the PTY for output:

```python
async def read_pty_output(self):
    while self.process and self.process.poll() is None:
        try:
            output = os.read(self.pty_master, 4096).decode('utf-8', errors='replace')
            if output:
                await self.broadcast({
                    'type': 'output',
                    'data': output,
                    'timestamp': time.time()
                })
        except BlockingIOError:
            await asyncio.sleep(0.01)
```

**Design decisions:**
- Non-blocking reads prevent hangs
- 4KB buffer size balances performance and responsiveness
- UTF-8 decoding with error replacement handles binary data gracefully
- Asyncio enables concurrent client handling

### 4. WebSocket Server

Built on aiohttp for async WebSocket support:

```python
async def handle_websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    broadcaster.clients.add(ws)
    
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            data = json.loads(msg.data)
            if data['type'] == 'input':
                broadcaster.send_input(data['data'])
```

**Protocol:**
- JSON-based message format
- Message types: `output`, `input`, `prompt`, `exit`, `history`
- Bidirectional communication for interactive terminals
- Automatic client cleanup on disconnect

### 5. Browser-Side Terminal Emulation

The JavaScript client handles two display modes:

#### Regular Mode
For simple command output (ls, cat, etc.):
```javascript
// Process backspaces
for (let i = 0; i < text.length; i++) {
    if (text.charCodeAt(i) === 8) { // Backspace
        processed = processed.slice(0, -1);
    } else {
        processed += text[i];
    }
}
```

#### Interactive Mode
For applications with cursor movement (vim, htop, etc.):
```javascript
function processTerminalOutput(text) {
    // Maintains virtual screen buffer
    // Processes ANSI escape sequences:
    // - ESC[nA - Cursor up
    // - ESC[K - Clear line
    // - ESC[2J - Clear screen
    // Updates screen buffer based on cursor movements
}
```

### 6. ANSI Escape Sequence Handling

term-cast processes various ANSI codes:

| Sequence | Meaning | Action |
|----------|---------|--------|
| `\x1b[nA` | Cursor up n lines | Adjust cursor position |
| `\x1b[K` | Clear to end of line | Clear buffer from cursor |
| `\x1b[2J` | Clear screen | Reset screen buffer |
| `\x1b[H` | Cursor home | Move cursor to 0,0 |
| `\x08` | Backspace | Remove previous character |

### 7. Input Handling

Input flows from browser → WebSocket → PTY → Process:

```python
def send_input(self, data):
    if self.pty_master:
        bytes_written = os.write(self.pty_master, data.encode('utf-8'))
```

Special character handling in JavaScript:
```javascript
.replace(/\\n/g, '\n')     // Newline
.replace(/\\r/g, '\r')     // Carriage return
.replace(/\\x03/g, String.fromCharCode(3))  // Ctrl+C
.replace(/\\x04/g, String.fromCharCode(4))  // Ctrl+D
```

### 8. Prompt Detection

Heuristic-based detection for when terminal needs input:

```python
def detect_prompt(self, output):
    prompt_patterns = [
        '[Y/n]', '[y/N]', '(y/n)', '(yes/no)',
        'password:', 'Password:', 'passphrase:',
        'Continue?', 'Proceed?', 'OK?'
    ]
    
    # Check patterns and line endings
    if output.rstrip().endswith((':', '?', '>', '$', '#', ']')):
        if time.time() - self.last_output_time > 0.5:
            return True
```

### 9. System Sleep Prevention

Platform-specific mechanisms to prevent system sleep:

- **macOS**: `caffeinate -d -i -s`
- **Linux**: `systemd-inhibit --what=idle:sleep:shutdown`
- **Windows**: `SetThreadExecutionState` API

## Data Flow

1. **Command Execution**
   ```
   User command → PTY slave → Process stdin
   ```

2. **Output Capture**
   ```
   Process stdout/stderr → PTY slave → PTY master → Python async read
   ```

3. **Broadcasting**
   ```
   Python → JSON encoding → WebSocket → All connected clients
   ```

4. **Display**
   ```
   WebSocket message → JavaScript processing → DOM update
   ```

5. **User Input**
   ```
   Browser input → WebSocket → Python → PTY master → Process stdin
   ```

## Performance Considerations

### Buffer Management
- Terminal output buffer limited to 10,000 lines server-side
- Browser DOM limited to 1,000 elements
- Screen buffer for interactive mode limited to 1,000 lines

### Network Optimization
- Messages batched when possible
- Ping/pong keepalive every 30 seconds
- Automatic reconnection with exponential backoff

### CPU Optimization
- Non-blocking I/O prevents thread starvation
- Async/await for concurrent client handling
- Efficient ANSI sequence processing (single pass)

## Security Considerations

1. **No Authentication**: term-cast has no built-in auth - use firewall/VPN
2. **Input Validation**: All input passed directly to PTY (potential for injection)
3. **Network Exposure**: Binds to 0.0.0.0 by default (all interfaces)
4. **Process Isolation**: Runs with user privileges, no sandboxing

## Limitations

1. **Terminal Size**: Fixed at 80x24, no dynamic resizing
2. **Color Support**: Basic ANSI colors only, no 24-bit color
3. **Scrollback**: Limited by buffer sizes
4. **File Transfer**: No support for terminal file transfer protocols
5. **Multiple Sessions**: Single command per instance

## Future Improvements

1. **Terminal Resizing**: Detect browser viewport and adjust PTY size
2. **Session Recording**: Save and replay terminal sessions
3. **Authentication**: Add basic auth or token-based access
4. **Compression**: Compress WebSocket messages for bandwidth savings
5. **Full xterm.js**: Replace custom renderer with xterm.js for better compatibility