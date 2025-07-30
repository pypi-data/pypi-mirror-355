import ast
import json
import asyncio
from typing import Any, Dict, cast, List, Union
import uuid
from anthropic.types.beta import BetaToolUseBlock
from computer_use_ootb_internal.computer_use_demo.tools import ComputerTool, ToolCollection
from computer_use_ootb_internal.computer_use_demo.tools.base import ToolResult, ToolError


class TeachmodeExecutor:
    def __init__(
        self, 
        selected_screen: int = 0,
        full_screen_game_mode: int = 0,  # 0: disabled, 1: starrail, 2: starrail browser
    ):
        self.selected_screen = selected_screen
        self.screen_bbox = self._get_screen_resolution()
        print("Screen BBox:", self.screen_bbox)
        
        self.tool_collection = ToolCollection(
            ComputerTool(selected_screen=selected_screen, is_scaling=False)
        )
        
        self.supported_action_type={
            # "showui_action": "anthropic_tool_action"
            "CLICK": 'key',  # TBD
            "RIGHT_CLICK": 'key',  # TBD
            "INPUT": "key",
            "MOVE": "key",
            "HOVER": "key",
            "ENTER": "key",  # TBD
            "ESC": "key",
            "ESCAPE": "key",
            "PRESS":  "key",
            "KEY": "key",
            "HOTKEY": "key",
            "DRAG": "key",
            "SCROLL": "key",
            "DOUBLE_CLICK": "key",
            "TRIPLE_CLICK": "key",
            "WAIT": "key",
        }

        self.full_screen_game_mode = full_screen_game_mode


    def __call__(self, action: Dict[str, Any]):
        """
        Executes a single, primitive action.
        The action is expected to be a dictionary with keys like 'action', 'text', 'coordinate'.
        """
        
        print("Executing single primitive action:", action)
        
        # Debug print screen bounds and max coordinates
        if hasattr(self, 'screen_bbox') and self.screen_bbox:
            x_min, y_min, x_max, y_max = self.screen_bbox
            print(f"[DEBUG] Screen bounds: ({x_min}, {y_min}) to ({x_max}, {y_max})")
            print(f"[DEBUG] Maximum action coordinates: x_max={x_max}, y_max={y_max}")
        
        # Handle the nested payload format: {"content": {"action": "CLICK", "position": [x, y], "value": ""}}
        if "content" in action:
            content = action["content"]
            action_type = content.get("action", "").upper()
            position = content.get("position")
            value = content.get("value", "")
            
            print(f"[DEBUG] Parsed from payload - action_type: {action_type}, position: {position}, value: '{value}'")
            
            # Map the action types to expected format
            action_mapping = {
                "CLICK": "left_click",
                "RIGHT_CLICK": "right_click", 
                "DOUBLE_CLICK": "double_click",
                "TRIPLE_CLICK": "triple_click",
                "INPUT": "type",
                "MOVE": "mouse_move",
                "HOVER": "mouse_move",
                "ENTER": "key",
                "ESC": "key",
                "ESCAPE": "key",
                "PRESS": "key",
                "KEY": "key",
                "HOTKEY": "key",
                "DRAG": "left_click_drag",
                "SCROLL": "scroll_down",  # Default to scroll_down, could be enhanced
                "WAIT": "wait",
            }
            
            mapped_action = action_mapping.get(action_type, action_type.lower())
            print(f"[DEBUG] Mapped action: {action_type} -> {mapped_action}")
            
            # Prepare the action dictionary in the expected format
            processed_action = {
                "action": mapped_action,
                "text": None,
                "coordinate": None
            }
            
            # Handle coordinate/position
            if position and isinstance(position, (list, tuple)) and len(position) == 2:
                processed_action["coordinate"] = position
                x, y = position
                print(f"[DEBUG] Action coordinates: x={x}, y={y}")
                
                # Check if coordinates are within screen bounds
                if hasattr(self, 'screen_bbox') and self.screen_bbox:
                    x_min, y_min, x_max, y_max = self.screen_bbox
                    if x < x_min or x >= x_max or y < y_min or y >= y_max:
                        print(f"[DEBUG] WARNING: Action coordinates ({x}, {y}) are outside screen bounds ({x_min}, {y_min}) to ({x_max}, {y_max})")
                    else:
                        print(f"[DEBUG] Action coordinates ({x}, {y}) are within screen bounds")
            
            # Handle text/value for input actions
            if action_type in ["INPUT", "ENTER", "ESC", "ESCAPE", "PRESS", "KEY", "HOTKEY"] and value:
                processed_action["text"] = value
            elif action_type == "ENTER":
                processed_action["text"] = "return"
            elif action_type in ["ESC", "ESCAPE"]:
                processed_action["text"] = "escape"
                
        else:
            # Handle direct format (backward compatibility)
            processed_action = {
                "action": action.get("action"), 
                "text": action.get("text"), 
                "coordinate": action.get("coordinate")
            }
            
            if processed_action["coordinate"]:
                x, y = processed_action["coordinate"]
                print(f"[DEBUG] Direct format coordinates: x={x}, y={y}")
        
        print(f"Processed action: {processed_action}")
        
        # The complex parsing and multi-action logic has been removed to support
        # executing only one action per API call. The game mode logic which
        # adds extra actions has also been bypassed to meet this requirement.

        sim_content_block = BetaToolUseBlock(
            id=f'toolu_{uuid.uuid4()}',
            input=processed_action,
            name='computer',
            type='tool_use'
        )

        # Run the synchronous tool execution directly
        tool_result = self.tool_collection.run(
            name=sim_content_block.name,
            tool_input=cast(dict[str, Any], sim_content_block.input),
        )
        
        result_message = {}
        if isinstance(tool_result, ToolResult):
            print(f"[teachmode_executor] tool_result: {tool_result}")
            result_message = {
                "role": "assistant", 
                "content": tool_result.output, 
                "type": tool_result.type, 
                "action_type": tool_result.action_base_type
            }
        elif isinstance(tool_result, ToolError):
            print(f"[teachmode_executor] tool_error: {tool_result}")
            result_message = {
                "role": "assistant", 
                "content": tool_result.output, 
                "type": "error", 
                "action_type": ""
            }
              
        return result_message
        
    
    # The _format_actor_output and _parse_actor_output methods are no longer used
    # and have been removed to simplify the executor.

    def _reformat_starrail_scrolls(self, action_list: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        converted_action_list = []
        for action in action_list:
            if action["action"] == "scroll_down":
                converted_action_list.append({"action": "sr_scroll_down", "text": None, "coordinate": None})
            elif action["action"] == "scroll_up":
                converted_action_list.append({"action": "sr_scroll_up", "text": None, "coordinate": None})
            else:
                converted_action_list.append(action)
        return converted_action_list
        
    def _add_starrail_alt_actions(self, action_list: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        parsed_action_list = []
        for action in action_list:
            if action["action"] in ["left_click", "mouse_move"]:
                parsed_action_list.append({"action": "key_down", "text": "alt", "coordinate": None})
                parsed_action_list.append(action)
                parsed_action_list.append({"action": "key_up", "text": "alt", "coordinate": None})
            else:
                parsed_action_list.append(action)
        return parsed_action_list

    def _reformat_starrail_browser_actions(self, action_list: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        converted_action_list = []
        for action in action_list:
            if action["action"] in ["left_click", "mouse_move", "key_down", "key_up"]:  # TODO: "right_click"
                action["action"] = f"{action['action']}_windll"
                converted_action_list.append(action)
            elif action["action"] == "scroll_down":
                converted_action_list.append({"action": "sr_scroll_down", "text": None, "coordinate": None})
            elif action["action"] == "scroll_up":
                converted_action_list.append({"action": "sr_scroll_up", "text": None, "coordinate": None})
            else:
                converted_action_list.append(action)
        return converted_action_list

    def _add_starrail_browser_alt_actions(self, action_list: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        parsed_action_list = []

        for action in action_list:
            if action["action"] in ["left_click", "mouse_move", "left_click_windll", "mouse_move_windll"]:
                parsed_action_list.append({"action": "key_down_windll", "text": "alt", "coordinate": None})
                parsed_action_list.append(action)
                parsed_action_list.append({"action": "key_up_windll", "text": "alt", "coordinate": None})
            else:
                parsed_action_list.append(action)

        return parsed_action_list


    def _get_screen_resolution(self):
        from screeninfo import get_monitors
        import platform
        if platform.system() == "Darwin":
            import Quartz  # uncomment this line if you are on macOS
        import subprocess
            
        # Detect platform
        system = platform.system()

        if system == "Windows":
            # Windows: Use screeninfo to get monitor details
            screens = get_monitors()

            # Sort screens by x position to arrange from left to right
            sorted_screens = sorted(screens, key=lambda s: s.x)

            if self.selected_screen < 0 or self.selected_screen >= len(screens):
                raise IndexError("Invalid screen index.")

            screen = sorted_screens[self.selected_screen]
            bbox = (screen.x, screen.y, screen.x + screen.width, screen.y + screen.height)

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

            if self.selected_screen < 0 or self.selected_screen >= len(screens):
                raise IndexError("Invalid screen index.")

            screen = sorted_screens[self.selected_screen]
            bbox = (screen['x'], screen['y'], screen['x'] + screen['width'], screen['y'] + screen['height'])

        else:  # Linux or other OS
            cmd = "xrandr | grep ' primary' | awk '{print $4}'"
            try:
                output = subprocess.check_output(cmd, shell=True).decode()
                resolution = output.strip().split()[0]
                width, height = map(int, resolution.split('x'))
                bbox = (0, 0, width, height)  # Assuming single primary screen for simplicity
            except subprocess.CalledProcessError:
                raise RuntimeError("Failed to get screen resolution on Linux.")
        
        return bbox


