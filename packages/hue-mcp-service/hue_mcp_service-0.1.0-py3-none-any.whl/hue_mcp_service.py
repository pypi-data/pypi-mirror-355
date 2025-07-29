#!/usr/bin/env python3
"""
Philips Hue MCP Service

A FastMCP service that provides tools and resources for controlling Philips Hue lights.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from qhue import Bridge, QhueException
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Philips Hue Controller")

class HueController:
    def __init__(self):
        self.bridge: Optional[Bridge] = None
        self.bridge_ip: Optional[str] = None
        self.username: Optional[str] = None
    
    def connect(self, bridge_ip: str, username: str) -> bool:
        """Connect to Hue bridge with given IP and username"""
        try:
            self.bridge = Bridge(bridge_ip, username)
            self.bridge_ip = bridge_ip
            self.username = username
            # Test connection by getting bridge info
            self.bridge.config()
            logger.info(f"Connected to Hue bridge at {bridge_ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to bridge: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to bridge"""
        return self.bridge is not None
    
    def get_lights(self) -> Dict[str, Any]:
        """Get all lights from the bridge"""
        if not self.is_connected():
            raise Exception("Not connected to Hue bridge")
        return self.bridge.lights()
    
    def get_light(self, light_id: str) -> Dict[str, Any]:
        """Get specific light info"""
        if not self.is_connected():
            raise Exception("Not connected to Hue bridge")
        return self.bridge.lights[light_id]()
    
    def set_light_state(self, light_id: str, **kwargs) -> bool:
        """Set light state with given parameters"""
        if not self.is_connected():
            raise Exception("Not connected to Hue bridge")
        try:
            self.bridge.lights[light_id].state(**kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to set light state: {e}")
            return False

# Global controller instance
hue_controller = HueController()

# Auto-connect if environment variables are set
def auto_connect():
    """Automatically connect to bridge if environment variables are set"""
    bridge_ip = os.getenv('HUE_BRIDGE_IP')
    username = os.getenv('HUE_USERNAME')
    
    if bridge_ip and username:
        logger.info(f"Auto-connecting to bridge at {bridge_ip}")
        success = hue_controller.connect(bridge_ip, username)
        if success:
            logger.info("Auto-connection successful!")
        else:
            logger.warning("Auto-connection failed")
        return success
    return False

@mcp.tool
def connect_to_bridge(bridge_ip: str, username: str) -> str:
    """
    Connect to a Philips Hue bridge.
    
    Args:
        bridge_ip: IP address of the Hue bridge
        username: Username/API key for the bridge
    
    Returns:
        Connection status message
    """
    success = hue_controller.connect(bridge_ip, username)
    if success:
        return f"Successfully connected to Hue bridge at {bridge_ip}"
    else:
        return f"Failed to connect to Hue bridge at {bridge_ip}"

@mcp.tool
def turn_light_on(light_id: str) -> str:
    """
    Turn on a specific light.
    
    Args:
        light_id: ID of the light to turn on
    
    Returns:
        Status message
    """
    try:
        success = hue_controller.set_light_state(light_id, on=True)
        return f"Light {light_id} turned on" if success else f"Failed to turn on light {light_id}"
    except Exception as e:
        return f"Error turning on light {light_id}: {str(e)}"

@mcp.tool
def turn_light_off(light_id: str) -> str:
    """
    Turn off a specific light.
    
    Args:
        light_id: ID of the light to turn off
    
    Returns:
        Status message
    """
    try:
        success = hue_controller.set_light_state(light_id, on=False)
        return f"Light {light_id} turned off" if success else f"Failed to turn off light {light_id}"
    except Exception as e:
        return f"Error turning off light {light_id}: {str(e)}"

@mcp.tool
def set_light_brightness(light_id: str, brightness: int) -> str:
    """
    Set brightness of a specific light.
    
    Args:
        light_id: ID of the light
        brightness: Brightness level (0-254)
    
    Returns:
        Status message
    """
    try:
        if not 0 <= brightness <= 254:
            return "Brightness must be between 0 and 254"
        
        success = hue_controller.set_light_state(light_id, bri=brightness)
        return f"Light {light_id} brightness set to {brightness}" if success else f"Failed to set brightness for light {light_id}"
    except Exception as e:
        return f"Error setting brightness for light {light_id}: {str(e)}"

@mcp.tool
def set_light_color(light_id: str, hue: int, saturation: int) -> str:
    """
    Set color of a specific light using hue and saturation.
    
    Args:
        light_id: ID of the light
        hue: Hue value (0-65535)
        saturation: Saturation value (0-254)
    
    Returns:
        Status message
    """
    try:
        if not 0 <= hue <= 65535:
            return "Hue must be between 0 and 65535"
        if not 0 <= saturation <= 254:
            return "Saturation must be between 0 and 254"
        
        success = hue_controller.set_light_state(light_id, hue=hue, sat=saturation)
        return f"Light {light_id} color set to hue:{hue}, sat:{saturation}" if success else f"Failed to set color for light {light_id}"
    except Exception as e:
        return f"Error setting color for light {light_id}: {str(e)}"

@mcp.tool
def set_light_xy_color(light_id: str, x: float, y: float) -> str:
    """
    Set color of a specific light using CIE xy coordinates.
    
    Args:
        light_id: ID of the light
        x: CIE x coordinate (0.0-1.0)
        y: CIE y coordinate (0.0-1.0)
    
    Returns:
        Status message
    """
    try:
        if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
            return "x and y coordinates must be between 0.0 and 1.0"
        
        success = hue_controller.set_light_state(light_id, xy=[x, y])
        return f"Light {light_id} color set to x:{x}, y:{y}" if success else f"Failed to set color for light {light_id}"
    except Exception as e:
        return f"Error setting color for light {light_id}: {str(e)}"

@mcp.resource("hue://lights")
def get_all_lights() -> str:
    """Get information about all lights connected to the bridge."""
    try:
        if not hue_controller.is_connected():
            return json.dumps({"error": "Not connected to Hue bridge"})
        
        lights = hue_controller.get_lights()
        return json.dumps(lights, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get lights: {str(e)}"})

@mcp.resource("hue://light/{light_id}")
def get_light_info(light_id: str) -> str:
    """Get detailed information about a specific light."""
    try:
        if not hue_controller.is_connected():
            return json.dumps({"error": "Not connected to Hue bridge"})
        
        light = hue_controller.get_light(light_id)
        return json.dumps(light, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get light {light_id}: {str(e)}"})

@mcp.resource("hue://bridge-status")
def get_bridge_status() -> str:
    """Get the current bridge connection status."""
    status = {
        "connected": hue_controller.is_connected(),
        "bridge_ip": hue_controller.bridge_ip,
        "username": hue_controller.username is not None
    }
    return json.dumps(status, indent=2)

if __name__ == "__main__":
    print("Starting Philips Hue MCP Service...")
    print("Available tools:")
    print("- connect_to_bridge: Connect to your Hue bridge")
    print("- turn_light_on/off: Control light power")
    print("- set_light_brightness: Set brightness (0-254)")
    print("- set_light_color: Set color using hue/saturation")
    print("- set_light_xy_color: Set color using CIE xy coordinates")
    print("\nAvailable resources:")
    print("- hue://lights: Get all lights")
    print("- hue://light/{id}: Get specific light info")
    print("- hue://bridge-status: Get connection status")
    
    # Try to auto-connect
    print("\nAttempting auto-connection...")
    if auto_connect():
        print("✓ Auto-connected to Hue bridge!")
    else:
        print("⚠ No auto-connection (use connect_to_bridge tool)")
    
    print("\nStarting MCP server...")
    mcp.run()