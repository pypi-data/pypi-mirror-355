#!/usr/bin/env python3
"""
Example usage of the Hue MCP Service.

This demonstrates how to use the MCP tools programmatically.
"""

import asyncio
import json
from hue_mcp_service import mcp, hue_controller

async def demo_hue_control():
    """Demonstrate the Hue MCP service functionality."""
    print("Hue MCP Service Demo")
    print("=" * 30)
    
    # Note: In a real scenario, you would get these from the user
    # or from a configuration file
    BRIDGE_IP = "192.168.1.123"  # Replace with your bridge IP
    USERNAME = "your-username-here"  # Replace with your username
    
    print(f"1. Connecting to bridge at {BRIDGE_IP}...")
    
    # Connect to bridge
    success = hue_controller.connect(BRIDGE_IP, USERNAME)
    if not success:
        print("Failed to connect! Please check your bridge IP and username.")
        print("Run setup_bridge.py to create a username if needed.")
        return
    
    print("✓ Connected successfully!")
    
    # Get all lights
    print("\n2. Getting all lights...")
    try:
        lights = hue_controller.get_lights()
        print(f"Found {len(lights)} lights:")
        for light_id, light_info in lights.items():
            name = light_info.get('name', 'Unknown')
            state = light_info.get('state', {})
            is_on = state.get('on', False)
            brightness = state.get('bri', 0)
            print(f"  Light {light_id}: {name} - {'ON' if is_on else 'OFF'} (brightness: {brightness})")
    except Exception as e:
        print(f"Error getting lights: {e}")
        return
    
    if not lights:
        print("No lights found!")
        return
    
    # Get the first light ID for demonstration
    first_light_id = list(lights.keys())[0]
    first_light_name = lights[first_light_id].get('name', 'Unknown')
    
    print(f"\n3. Demonstrating control with light {first_light_id} ({first_light_name})...")
    
    # Turn light on
    print("   Turning light ON...")
    success = hue_controller.set_light_state(first_light_id, on=True)
    if success:
        print("   ✓ Light turned on")
    else:
        print("   ✗ Failed to turn light on")
    
    await asyncio.sleep(2)
    
    # Set brightness
    print("   Setting brightness to 50%...")
    success = hue_controller.set_light_state(first_light_id, bri=127)
    if success:
        print("   ✓ Brightness set")
    else:
        print("   ✗ Failed to set brightness")
    
    await asyncio.sleep(2)
    
    # Set color to red
    print("   Setting color to red...")
    success = hue_controller.set_light_state(first_light_id, hue=0, sat=254)
    if success:
        print("   ✓ Color set to red")
    else:
        print("   ✗ Failed to set color")
    
    await asyncio.sleep(2)
    
    # Set color to blue
    print("   Setting color to blue...")
    success = hue_controller.set_light_state(first_light_id, hue=43690, sat=254)
    if success:
        print("   ✓ Color set to blue")
    else:
        print("   ✗ Failed to set color")
    
    await asyncio.sleep(2)
    
    # Turn light off
    print("   Turning light OFF...")
    success = hue_controller.set_light_state(first_light_id, on=False)
    if success:
        print("   ✓ Light turned off")
    else:
        print("   ✗ Failed to turn light off")
    
    print("\n4. Demo complete! ✓")
    print("\nTo use this as an MCP service, run:")
    print("   python hue_mcp_service.py")
    print("\nThen use the MCP tools in your AI application.")

def main():
    """Main function to run the demo."""
    print("This is a demo script to test the Hue MCP service functionality.")
    print("Make sure to update BRIDGE_IP and USERNAME in this file first!")
    print()
    
    response = input("Do you want to run the demo? (y/n): ").lower().strip()
    if response == 'y':
        asyncio.run(demo_hue_control())
    else:
        print("Demo cancelled.")

if __name__ == "__main__":
    main()