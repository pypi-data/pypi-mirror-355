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
    """Take a screenshot of a hardcoded 1920x1080 area starting from top-left corner (0,0)."""
    
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"screenshot_{uuid4().hex}.png"

    # Get actual screen size for debugging
    try:
        actual_screen_width, actual_screen_height = _get_screen_size(selected_screen)
        print(f"[DEBUG] Actual screen size: {actual_screen_width}x{actual_screen_height}")
    except Exception as e:
        print(f"[DEBUG] Could not get actual screen size: {e}")
        actual_screen_width, actual_screen_height = "unknown", "unknown"

    # Hardcode the screenshot area to 1920x1080 starting from top-left corner
    hardcoded_region = (0, 0, 1920, 1080)
    print(f"[DEBUG] Hardcoded capture region: {hardcoded_region} (x, y, width, height)")
    print(f"[DEBUG] Capture area: 1920x1080 vs Actual screen: {actual_screen_width}x{actual_screen_height}")
    
    try:
        # Take screenshot of the hardcoded region (0,0) to (1920,1080)
        screenshot = pyautogui.screenshot(region=hardcoded_region)
        print(f"[DEBUG] Screenshot captured using region method, size: {screenshot.size}")
    except Exception as e:
        print(f"[DEBUG] Region method failed: {e}")
        # Fallback: take full screenshot and crop to the hardcoded area
        try:
            full_screenshot = pyautogui.screenshot()
            print(f"[DEBUG] Full screenshot size: {full_screenshot.size}")
            # Crop to the hardcoded 1920x1080 area from top-left
            screenshot = full_screenshot.crop((0, 0, 1920, 1080))
            print(f"[DEBUG] Screenshot cropped using fallback method, size: {screenshot.size}")
        except Exception as e2:
            raise ToolError(
                output=f"Failed to capture hardcoded 1920x1080 screenshot. Region method: {e}, Crop method: {e2}",
                action_base_type="screenshot"
            )

    if screenshot is None:
        raise ToolError(
            output="Screenshot capture returned None",
            action_base_type="screenshot"
        )

    print(f"[DEBUG] Final screenshot size before any resizing: {screenshot.size}")

    # No resizing needed since we're already capturing exactly 1920x1080
    # But keep the resize logic in case it's still needed for some reason
    if resize and (target_width != 1920 or target_height != 1080):
        print(f"[DEBUG] Resizing screenshot from {screenshot.size} to {target_width}x{target_height}")
        screenshot = screenshot.resize((target_width, target_height))
        print(f"[DEBUG] Final screenshot size after resizing: {screenshot.size}")

    # Save the screenshot
    screenshot.save(str(path))
    print(f"[DEBUG] Screenshot saved to: {path}")

    if path.exists():
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
