# Philips Hue MCP Service

A FastMCP service that provides tools and resources for controlling Philips Hue lights through the Model Context Protocol.

## Installation

1. Install dependencies:
```bash
pip install fastmcp qhue requests
```

Or install from the project directory:
```bash
pip install -e .
```

## Setup

### 1. Find your Hue Bridge IP
- Open the Philips Hue app on your phone
- Go to Settings > My Hue System > [Your Bridge Name]
- Note the IP address

### 2. Create a Username/API Key
You need to create a username (API key) for your bridge:

1. Press the physical button on your Hue bridge
2. Within 30 seconds, run this Python script:

```python
import requests
import json

bridge_ip = "192.168.1.123"  # Replace with your bridge IP
response = requests.post(f"http://{bridge_ip}/api", 
                        json={"devicetype": "hue_mcp_service#user"})
print(json.dumps(response.json(), indent=2))
```

3. Save the returned username/API key

## Usage

### Running the Service

```bash
python hue_mcp_service.py
```

### Available Tools

- `connect_to_bridge(bridge_ip, username)` - Connect to your Hue bridge
- `turn_light_on(light_id)` - Turn on a specific light
- `turn_light_off(light_id)` - Turn off a specific light
- `set_light_brightness(light_id, brightness)` - Set brightness (0-254)
- `set_light_color(light_id, hue, saturation)` - Set color using hue/saturation values
- `set_light_xy_color(light_id, x, y)` - Set color using CIE xy coordinates

### Available Resources

- `lights` - Get information about all lights
- `light/{light_id}` - Get detailed information about a specific light
- `bridge-status` - Get current bridge connection status

### Example Usage

First, connect to your bridge:
```python
connect_to_bridge("192.168.1.123", "your-username-here")
```

Then control your lights:
```python
# Turn on light 1
turn_light_on("1")

# Set brightness to 50%
set_light_brightness("1", 127)

# Set to red color
set_light_color("1", 0, 254)
```

## Color Values

### Hue and Saturation
- **Hue**: 0-65535 (color wheel position)
  - 0: Red
  - 10922: Yellow  
  - 21845: Green
  - 32768: Cyan
  - 43690: Blue
  - 54613: Magenta
- **Saturation**: 0-254 (color intensity, 0=white, 254=full color)

### CIE xy Coordinates
- **x, y**: 0.0-1.0 (precise color specification in CIE color space)
- Common colors:
  - Red: (0.675, 0.322)
  - Green: (0.4091, 0.518)
  - Blue: (0.167, 0.04)
  - White: (0.3127, 0.329)

## Requirements

- Python 3.8+
- FastMCP 2.0+
- qhue 2.0+
- requests 2.25+