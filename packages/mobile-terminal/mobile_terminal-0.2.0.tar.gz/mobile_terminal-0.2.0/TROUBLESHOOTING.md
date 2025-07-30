# term-cast Troubleshooting

## Connection Stuck on "Connecting..."

If your phone shows "Connecting..." and never connects, try these steps:

### 1. Check Dependencies
First, make sure you have the required Python packages:

```bash
pip install aiohttp aiofiles
```

### 2. Test with Simple Version
Try the simplified test version first:

```bash
python simple_test.py
```

Then open http://localhost:8080 on your phone.

### 3. Check Firewall
Make sure your firewall isn't blocking port 8080:

**macOS:**
```bash
sudo pfctl -d  # Temporarily disable firewall
```

**Linux:**
```bash
sudo ufw allow 8080
```

### 4. Verify Same Network
Ensure both devices are on the same WiFi network:

**On laptop:**
```bash
ifconfig | grep "inet "  # Check your IP
```

**On phone:**
- Go to WiFi settings
- Check you're on the same network
- Try accessing http://YOUR_LAPTOP_IP:8080

### 5. Try Different Port
Port 8080 might be in use:

```bash
python term_cast.py --port 8888 ls
```

### 6. Debug Mode
Check browser console on phone:
1. Connect phone to computer
2. Open Safari/Chrome dev tools
3. Check for WebSocket errors

### 7. Common Fixes

**Fix 1: Install specific aiohttp version**
```bash
pip install aiohttp==3.8.6
```

**Fix 2: Use localhost first**
Test on laptop browser first:
```bash
python term_cast.py
# Open http://localhost:8080 on laptop
```

**Fix 3: Check Python version**
Requires Python 3.7+:
```bash
python --version
```

### 8. Alternative: Use ngrok
If local network isn't working, use ngrok:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# In terminal 1:
python term_cast.py

# In terminal 2:
ngrok http 8080

# Use the ngrok URL on your phone
```

## Still Not Working?

Try the debug script:
```bash
python debug.py
```

This will show:
- Python version
- aiohttp version  
- If basic server works

## Error Messages

### "WebSocket connection failed"
- Check firewall
- Try different port
- Verify same network

### "Failed to create connection"
- Dependencies missing
- Port already in use
- Permission issues

### "Connection timeout"
- Network issue
- Firewall blocking
- Wrong IP address