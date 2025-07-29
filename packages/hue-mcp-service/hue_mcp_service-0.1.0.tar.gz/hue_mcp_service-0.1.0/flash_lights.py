#!/usr/bin/env python3
"""
Flash all Hue lights 5 times
"""

import asyncio
import time
from hue_mcp_service import hue_controller, auto_connect

async def flash_all_lights():
    """Flash all lights 5 times"""
    print("Flashing all lights 5 times...")
    
    # Connect to bridge
    if not hue_controller.is_connected():
        print("Connecting to bridge...")
        if not auto_connect():
            print("Failed to connect to bridge!")
            return
    
    # Get all lights
    try:
        lights = hue_controller.get_lights()
        light_ids = list(lights.keys())
        print(f"Found {len(light_ids)} lights")
        
        # Store original states and check capabilities
        original_states = {}
        color_capable_lights = []
        
        for light_id in light_ids:
            light_info = lights[light_id]
            state = light_info.get('state', {})
            original_states[light_id] = {
                'on': state.get('on', False),
                'hue': state.get('hue'),
                'sat': state.get('sat'),
                'bri': state.get('bri'),
                'xy': state.get('xy')
            }
            
            # Check if light supports color (has hue/sat in state)
            if 'hue' in state and 'sat' in state:
                color_capable_lights.append(light_id)
        
        print(f"Color-capable lights: {len(color_capable_lights)}/{len(light_ids)}")
        
        # Flash 5 times with RED color for color lights, bright white for others
        for flash_num in range(1, 6):
            print(f"Flash {flash_num}/5 - RED for color lights, bright white for others...")
            
            # Turn all lights ON
            for light_id in light_ids:
                if light_id in color_capable_lights:
                    # Color light: RED (hue=0, sat=254 for full red)
                    hue_controller.set_light_state(light_id, on=True, hue=0, sat=254, bri=254)
                else:
                    # White-only light: just bright white
                    hue_controller.set_light_state(light_id, on=True, bri=254)
            
            await asyncio.sleep(0.3)  # On for 0.3 seconds
            
            # Turn all lights OFF
            for light_id in light_ids:
                hue_controller.set_light_state(light_id, on=False)
            
            await asyncio.sleep(0.3)  # Off for 0.3 seconds
        
        # Restore original states (color, brightness, and on/off)
        print("Restoring original light states...")
        for light_id, original_state in original_states.items():
            # Build the restore command with original values
            restore_params = {'on': original_state['on']}
            
            # Only restore color/brightness if the light was originally on
            if original_state['on']:
                if original_state['hue'] is not None:
                    restore_params['hue'] = original_state['hue']
                if original_state['sat'] is not None:
                    restore_params['sat'] = original_state['sat']
                if original_state['bri'] is not None:
                    restore_params['bri'] = original_state['bri']
                if original_state['xy'] is not None:
                    restore_params['xy'] = original_state['xy']
            
            hue_controller.set_light_state(light_id, **restore_params)
        
        print("✓ Flash sequence complete!")
        
    except Exception as e:
        print(f"Error during flash sequence: {e}")

if __name__ == "__main__":
    asyncio.run(flash_all_lights())