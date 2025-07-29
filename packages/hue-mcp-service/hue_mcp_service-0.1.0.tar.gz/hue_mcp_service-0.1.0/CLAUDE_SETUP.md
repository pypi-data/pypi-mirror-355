# Claude Desktop MCP Setup Guide

This guide walks you through setting up the Philips Hue MCP service with Claude Desktop.

## Prerequisites

1. **Claude Desktop installed** on your system
2. **Philips Hue bridge** connected to your network
3. **Python 3.8+** installed
4. **Hue MCP service** installed (follow main README.md first)

## Step 1: Complete Basic Setup

First, make sure you've completed the basic setup from the main README:

1. Install dependencies: `pip install fastmcp qhue requests`
2. Run bridge setup: `python setup_bridge.py`
3. Test the service: `python hue_mcp_service.py`

## Step 2: Add Environment Variables

Add your Hue credentials to your shell configuration file:

### For Zsh (macOS default):
```bash
echo 'export HUE_BRIDGE_IP=your.bridge.ip.here' >> ~/.zshrc
echo 'export HUE_USERNAME=your-username-here' >> ~/.zshrc
source ~/.zshrc
```

### For Bash:
```bash
echo 'export HUE_BRIDGE_IP=your.bridge.ip.here' >> ~/.bashrc
echo 'export HUE_USERNAME=your-username-here' >> ~/.bashrc
source ~/.bashrc
```

Replace `your.bridge.ip.here` and `your-username-here` with the actual values from your setup.

## Step 3: Configure Claude Desktop

### Create the configuration directory:
```bash
mkdir -p ~/.config/claude-desktop
```

### Create or edit the configuration file:
```bash
nano ~/.config/claude-desktop/claude_desktop_config.json
```

### Add the Hue MCP service configuration:

**Option A: Using environment variables (recommended)**
```json
{
  "mcpServers": {
    "hue-mcp-service": {
      "command": "python",
      "args": ["/full/path/to/hue-mcp-service/hue_mcp_service.py"],
      "env": {
        "HUE_BRIDGE_IP": "your.bridge.ip.here",
        "HUE_USERNAME": "your-username-here"
      }
    }
  }
}
```

**Option B: Inheriting from shell environment**
```json
{
  "mcpServers": {
    "hue-mcp-service": {
      "command": "python",
      "args": ["/full/path/to/hue-mcp-service/hue_mcp_service.py"]
    }
  }
}
```

> **Important**: Replace `/full/path/to/hue-mcp-service/` with the actual absolute path to your installation.

### Find your installation path:
```bash
cd hue-mcp-service
pwd
```

## Step 4: Restart Claude Desktop

Close and restart Claude Desktop completely for the configuration to take effect.

## Step 5: Test the Integration

In Claude Desktop, you should now be able to:

1. **Check connection status**: Ask Claude to check the bridge status
2. **Control lights**: Ask Claude to turn lights on/off, change colors, etc.
3. **Get light information**: Ask Claude to list all your lights

### Example Commands to Try:

- "Can you check if the Hue bridge is connected?"
- "Turn on all the lights"
- "Set the living room light to blue"
- "Show me all my lights and their current status"
- "Make all lights flash red 3 times"

## Available Tools

Once configured, Claude will have access to these tools:

- `connect_to_bridge(bridge_ip, username)` - Connect to bridge
- `turn_light_on(light_id)` - Turn on a specific light
- `turn_light_off(light_id)` - Turn off a specific light  
- `set_light_brightness(light_id, brightness)` - Set brightness (0-254)
- `set_light_color(light_id, hue, saturation)` - Set color
- `set_light_xy_color(light_id, x, y)` - Set precise color

## Available Resources

- `hue://lights` - Get all lights information
- `hue://light/{id}` - Get specific light details
- `hue://bridge-status` - Check connection status

## Troubleshooting

### MCP Server Not Found
- Check that the path in `claude_desktop_config.json` is correct and absolute
- Ensure Python is available in your PATH
- Verify the script is executable: `python /path/to/hue_mcp_service.py`

### Connection Issues
- Verify environment variables are set: `echo $HUE_BRIDGE_IP`
- Test the service manually: `python hue_mcp_service.py`
- Check your bridge IP hasn't changed

### Permission Issues
- Ensure the script file is readable
- Check that your username is still valid with the bridge

### Debug Mode
Enable debug logging by modifying the script's logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- Your Hue credentials are stored in environment variables or the config file
- The config file is local to your machine and not shared with Anthropic
- Consider using environment variables for better security
- Never commit actual credentials to version control

## Configuration Examples

### Multiple Hue Bridges
```json
{
  "mcpServers": {
    "hue-main": {
      "command": "python",
      "args": ["/path/to/hue_mcp_service.py"],
      "env": {
        "HUE_BRIDGE_IP": "192.168.1.100",
        "HUE_USERNAME": "username1"
      }
    },
    "hue-office": {
      "command": "python", 
      "args": ["/path/to/hue_mcp_service.py"],
      "env": {
        "HUE_BRIDGE_IP": "192.168.1.101",
        "HUE_USERNAME": "username2"
      }
    }
  }
}
```

### With Additional MCP Services
```json
{
  "mcpServers": {
    "hue-mcp-service": {
      "command": "python",
      "args": ["/path/to/hue_mcp_service.py"]
    },
    "other-mcp-service": {
      "command": "node",
      "args": ["/path/to/other-service/server.js"]
    }
  }
}
```