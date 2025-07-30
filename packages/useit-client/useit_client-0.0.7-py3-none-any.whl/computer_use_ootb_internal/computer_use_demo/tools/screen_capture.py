import subprocess
import base64
from pathlib import Path
import pyautogui  # Replace PIL.ImageGrab with pyautogui
from uuid import uuid4
from screeninfo import get_monitors
import platform
if platform.system() == "Darwin":
    import Quartz  # uncomment this line if you are on macOS
    
from .base import BaseAnthropicTool, ToolError, ToolResult


OUTPUT_DIR = "./tmp/outputs"

def get_screenshot(selected_screen: int = 0, resize: bool = True, target_width: int = 1920, target_height: int = 1080):
    # print(f"get_screenshot selected_screen: {selected_screen}")
    
    # Get screen width and height using Windows command
    display_num = None
    offset_x = 0
    offset_y = 0
    selected_screen = selected_screen   
    width, height = _get_screen_size()    

    """Take a screenshot of the current screen and return a ToolResult with the base64 encoded image."""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"screenshot_{uuid4().hex}.png"

    # Detect platform
    system = platform.system()

    if system == "Windows":
        # Windows: Use screeninfo to get monitor details
        screens = get_monitors()

        # Sort screens by x position to arrange from left to right
        sorted_screens = sorted(screens, key=lambda s: s.x)

        if selected_screen < 0 or selected_screen >= len(screens):
            raise IndexError("Invalid screen index.")

        screen = sorted_screens[selected_screen]
        # Store screen info for cropping
        screen_info = {
            'x': screen.x,
            'y': screen.y, 
            'width': screen.width,
            'height': screen.height
        }

    elif system == "Darwin":  # macOS
        # macOS: Use Quartz to get monitor details
        max_displays = 32  # Maximum number of displays to handle
        active_displays = Quartz.CGGetActiveDisplayList(max_displays, None, None)[1]

        # Get the display bounds (resolution) for each active display
        screens = []
        for display_id in active_displays:
            bounds = Quartz.CGDisplayBounds(display_id)
            screens.append({
                'id': display_id,
                'x': int(bounds.origin.x),
                'y': int(bounds.origin.y),
                'width': int(bounds.size.width),
                'height': int(bounds.size.height),
                'is_primary': Quartz.CGDisplayIsMain(display_id)  # Check if this is the primary display
            })

        # Sort screens by x position to arrange from left to right
        sorted_screens = sorted(screens, key=lambda s: s['x'])
        # print(f"Darwin sorted_screens: {sorted_screens}")

        if selected_screen < 0 or selected_screen >= len(screens):
            raise IndexError("Invalid screen index.")

        screen = sorted_screens[selected_screen]
        
        # Store screen info for cropping
        screen_info = {
            'x': screen['x'],
            'y': screen['y'],
            'width': screen['width'],
            'height': screen['height']
        }

    else:  # Linux or other OS
        cmd = "xrandr | grep ' primary' | awk '{print $4}'"
        try:
            output = subprocess.check_output(cmd, shell=True).decode()
            resolution = output.strip().split()[0]
            width, height = map(int, resolution.split('x'))
            screen_info = {'x': 0, 'y': 0, 'width': width, 'height': height}
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to get screen resolution on Linux.")

    # Take screenshot using pyautogui - try different approaches
    screenshot = None
    
    # Method 1: Try with region (original approach)
    try:
        region = (screen_info['x'], screen_info['y'], screen_info['width'], screen_info['height'])
        screenshot = pyautogui.screenshot(region=region)
    except Exception as e1:
        print(f"Method 1 (region) failed: {e1}")
        
        # Method 2: Try full screenshot and crop
        try:
            full_screenshot = pyautogui.screenshot()
            # Crop to the specific screen area
            left = screen_info['x']
            top = screen_info['y'] 
            right = left + screen_info['width']
            bottom = top + screen_info['height']
            screenshot = full_screenshot.crop((left, top, right, bottom))
        except Exception as e2:
            print(f"Method 2 (crop) failed: {e2}")
            
            # Method 3: Try without region (fallback to primary screen)
            try:
                screenshot = pyautogui.screenshot()
                # If we're not on the primary screen, this might not be ideal, but it's a fallback
                if selected_screen != 0:
                    print(f"Warning: Falling back to full screenshot instead of screen {selected_screen}")
            except Exception as e3:
                # All methods failed
                raise ToolError(
                    output=f"Failed to capture screenshot using all methods. Region: {e1}, Crop: {e2}, Full: {e3}",
                    action_base_type="screenshot"
                )

    if screenshot is None:
        raise ToolError(
            output="Screenshot capture returned None",
            action_base_type="screenshot"
        )

    # Set offsets (for potential future use)
    offset_x = screen_info['x']
    offset_y = screen_info['y']

    # Resize if requested
    if resize:
        screenshot = screenshot.resize((target_width, target_height))

    # Save the screenshot
    screenshot.save(str(path))

    if path.exists():
        # Return a ToolResult instance instead of a dictionary
        return screenshot, str(path)
    
    raise ToolError(
        output=f"Failed to take screenshot: {path} does not exist.",
        action_base_type="screenshot"
    )
    
    


def _get_screen_size(selected_screen: int = 0):
    if platform.system() == "Windows":
        # Use screeninfo to get primary monitor on Windows
        screens = get_monitors()

        # Sort screens by x position to arrange from left to right
        sorted_screens = sorted(screens, key=lambda s: s.x)
        if selected_screen is None:
            primary_monitor = next((m for m in get_monitors() if m.is_primary), None)
            return primary_monitor.width, primary_monitor.height
        elif selected_screen < 0 or selected_screen >= len(screens):
            raise IndexError("Invalid screen index.")
        else:
            screen = sorted_screens[selected_screen]
            return screen.width, screen.height
    elif platform.system() == "Darwin":
        # macOS part using Quartz to get screen information
        max_displays = 32  # Maximum number of displays to handle
        active_displays = Quartz.CGGetActiveDisplayList(max_displays, None, None)[1]

        # Get the display bounds (resolution) for each active display
        screens = []
        for display_id in active_displays:
            bounds = Quartz.CGDisplayBounds(display_id)
            screens.append({
                'id': display_id,
                'x': int(bounds.origin.x),
                'y': int(bounds.origin.y),
                'width': int(bounds.size.width),
                'height': int(bounds.size.height),
                'is_primary': Quartz.CGDisplayIsMain(display_id)  # Check if this is the primary display
            })

        # Sort screens by x position to arrange from left to right
        sorted_screens = sorted(screens, key=lambda s: s['x'])

        if selected_screen is None:
            # Find the primary monitor
            primary_monitor = next((screen for screen in screens if screen['is_primary']), None)
            if primary_monitor:
                return primary_monitor['width'], primary_monitor['height']
            else:
                raise RuntimeError("No primary monitor found.")
        elif selected_screen < 0 or selected_screen >= len(screens):
            raise IndexError("Invalid screen index.")
        else:
            # Return the resolution of the selected screen
            screen = sorted_screens[selected_screen]
            return screen['width'], screen['height']

    else:  # Linux or other OS
        cmd = "xrandr | grep ' primary' | awk '{print $4}'"
        try:
            output = subprocess.check_output(cmd, shell=True).decode()
            resolution = output.strip().split()[0]
            width, height = map(int, resolution.split('x'))
            return width, height
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to get screen resolution on Linux.")
