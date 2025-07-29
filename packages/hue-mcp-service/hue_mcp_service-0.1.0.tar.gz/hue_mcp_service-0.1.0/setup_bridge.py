#!/usr/bin/env python3
"""
Setup script to help users create a Hue bridge username/API key.
"""

import requests
import json
import time
import sys
from typing import Optional

def discover_bridge() -> Optional[str]:
    """Attempt to discover Hue bridge IP address."""
    print("Attempting to discover Hue bridge...")
    try:
        response = requests.get("https://discovery.meethue.com/", timeout=5)
        if response.status_code == 200:
            bridges = response.json()
            if bridges:
                bridge_ip = bridges[0]["internalipaddress"]
                print(f"Found Hue bridge at: {bridge_ip}")
                return bridge_ip
        print("No bridge found via discovery service.")
    except Exception as e:
        print(f"Discovery failed: {e}")
    return None

def create_username(bridge_ip: str) -> Optional[str]:
    """Create a username for the bridge."""
    print(f"\nCreating username for bridge at {bridge_ip}")
    print("Please press the physical button on your Hue bridge NOW!")
    print("You have 30 seconds...")
    
    for i in range(30, 0, -1):
        print(f"Trying in {i} seconds... ", end="", flush=True)
        time.sleep(1)
        print()
        
        try:
            response = requests.post(
                f"http://{bridge_ip}/api",
                json={"devicetype": "hue_mcp_service#setup"}
            )
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                if "success" in result[0]:
                    username = result[0]["success"]["username"]
                    print(f"\nSuccess! Username created: {username}")
                    return username
                elif "error" in result[0]:
                    error = result[0]["error"]
                    if error["type"] == 101:
                        continue  # Link button not pressed
                    else:
                        print(f"Error: {error['description']}")
                        return None
        except Exception as e:
            print(f"Request failed: {e}")
            continue
    
    print("\nTimeout! Please run the script again and press the bridge button.")
    return None

def test_connection(bridge_ip: str, username: str) -> bool:
    """Test the connection with the new username."""
    try:
        response = requests.get(f"http://{bridge_ip}/api/{username}/lights")
        if response.status_code == 200:
            lights = response.json()
            if isinstance(lights, dict) and not lights.get("error"):
                print(f"Connection test successful! Found {len(lights)} lights.")
                return True
        print("Connection test failed.")
        return False
    except Exception as e:
        print(f"Connection test error: {e}")
        return False

def main():
    print("Philips Hue Bridge Setup")
    print("=" * 30)
    
    # Get bridge IP
    bridge_ip = discover_bridge()
    if not bridge_ip:
        bridge_ip = input("Enter your Hue bridge IP address: ").strip()
        if not bridge_ip:
            print("Bridge IP is required!")
            sys.exit(1)
    
    # Create username
    username = create_username(bridge_ip)
    if not username:
        print("Failed to create username!")
        sys.exit(1)
    
    # Test connection
    if test_connection(bridge_ip, username):
        print("\n" + "=" * 50)
        print("Setup complete! Use these values:")
        print(f"Bridge IP: {bridge_ip}")
        print(f"Username: {username}")
        print("\nYou can now run:")
        print(f'python hue_mcp_service.py')
        print("\nAnd connect using:")
        print(f'connect_to_bridge("{bridge_ip}", "{username}")')
        print("=" * 50)
    else:
        print("Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()