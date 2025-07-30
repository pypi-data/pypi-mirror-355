# term-cast Quick Start

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/term-cast.git
cd term-cast

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Basic Usage

### 1. Run any command
```bash
python term_cast.py npm install
```

### 2. Run the demo
```bash
python term_cast.py ./examples/demo.sh
```

### 3. Monitor your shell
```bash
python term_cast.py
# This starts an interactive shell session
```

### 4. Monitor AI tools
```bash
python term_cast.py claude-code
```

## On Your Phone

1. Make sure your phone is on the same WiFi network as your laptop
2. Open the URL shown in terminal (e.g., http://192.168.1.42:8080)
3. You'll see your terminal output in real-time

### Two Modes of Operation:

#### 1. **Automatic Mode** (Default)
- Waits for the terminal to need input
- When input is needed (Y/N prompts, passwords, etc.):
  - Phone vibrates
  - Notification appears
  - Input box appears automatically
  - Quick buttons for common responses

#### 2. **Interactive Mode** (Full Control)
- Tap the keyboard button (⌨️) in bottom-right corner
- Button turns green (💬) - you're now in interactive mode
- Type ANY command anytime, just like SSH
- Perfect for:
  - Running commands (`ls`, `cd`, `git status`, etc.)
  - Navigating directories
  - Editing files with nano/vim
  - Full terminal control

### Quick Buttons Available:
- **Y** - Send "y" and Enter
- **N** - Send "n" and Enter  
- **Enter ↵** - Send Enter key
- **Ctrl+C** - Cancel/interrupt
- **Ctrl+D** - End input/logout
- **Ctrl+Z** - Suspend process

## Features

- **Real-time streaming** - See terminal output instantly
- **Input detection** - Get notified when input is needed
- **Quick responses** - Buttons for common inputs (Y/N/Enter)
- **Sleep prevention** - Laptop stays awake
- **Mobile optimized** - Works great on phones
- **Secure** - Local network only

## Tips

- Grant notification permissions for alerts
- Add to home screen for app-like experience
- Works with any command that needs occasional input
- Perfect for long-running deployments or updates