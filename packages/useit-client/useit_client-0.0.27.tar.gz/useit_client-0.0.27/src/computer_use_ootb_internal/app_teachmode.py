import argparse
import time
import json
from datetime import datetime
import threading
import requests
import platform  # Add platform import
import pyautogui  # Add pyautogui import
import webbrowser # Add webbrowser import
import os # Import os for path joining
import logging # Import logging
import importlib # For dynamic imports
import pkgutil # To find modules
import sys # For logging setup
import traceback # For logging setup
from logging.handlers import RotatingFileHandler # For logging setup
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from computer_use_ootb_internal.computer_use_demo.tools.computer import get_screen_details
from computer_use_ootb_internal.computer_use_demo.executor.teachmode_executor import TeachmodeExecutor
import uvicorn # Assuming uvicorn is used to run FastAPI
import concurrent.futures
import asyncio

# --- App Logging Setup ---
try:
    # NEW: Log to a subdirectory under ProgramData/OOTBGuardService, specific to the current user
    program_data_dir = os.environ.get('PROGRAMDATA', 'C:/ProgramData') # Use C:/ProgramData as a fallback
    guard_service_log_base_dir = os.path.join(program_data_dir, 'OOTBGuardService')
    
    current_username = os.getenv('USERNAME', 'unknown_user_app') # Get current username, fallback
    app_logs_subfolder = "UserSessionLogs" # Subfolder for these app logs
    
    log_dir = os.path.join(guard_service_log_base_dir, app_logs_subfolder, current_username)
    
    os.makedirs(log_dir, exist_ok=True) # Create user-specific log directory
    log_file = os.path.join(log_dir, 'ootb_app.log')

    log_format = '%(asctime)s - %(levelname)s - %(process)d - %(threadName)s - %(message)s'
    log_level = logging.INFO # Or logging.DEBUG for more detail

    # Setup the rotating file handler
    rotating_file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    rotating_file_handler.setFormatter(logging.Formatter(log_format))

    # Setup the console handler
    console_handler_for_basic_config = logging.StreamHandler(sys.stdout)
    console_handler_for_basic_config.setFormatter(logging.Formatter(log_format))

    # Configure root logger with both file and console handlers
    # This replaces the old basicConfig and the subsequent addHandler calls for file and console
    logging.basicConfig(level=log_level, handlers=[rotating_file_handler, console_handler_for_basic_config])
    
    logging.info("="*20 + " OOTB App Starting " + "="*20)
    logging.info(f"Logging to file: {log_file}") # Explicitly log the path
    logging.info(f"Running with args: {sys.argv}")
    logging.info(f"Python Executable: {sys.executable}")
    logging.info(f"Working Directory: {os.getcwd()}")
    logging.info(f"User: {current_username}") # Log the username being used for the path

except Exception as log_setup_e:
    print(f"FATAL: Failed to set up logging: {log_setup_e}")
    traceback.print_exc() # Print traceback for debugging log setup failure

# --- Get the root logger ---
# The root logger is now fully configured by basicConfig above.
# The following sections for re-adding file handler and console handler are no longer needed.
root_logger = logging.getLogger()
# root_logger.setLevel(log_level) # This was redundant as basicConfig sets the level.

# --- File Handler (as before) ---
# REMOVED - This was redundant as rotating_file_handler is now passed to basicConfig.
# file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
# file_handler.setFormatter(logging.Formatter(log_format))
# root_logger.addHandler(file_handler)

# --- Console Handler (New) ---
# REMOVED - This was redundant as console_handler_for_basic_config is now passed to basicConfig.
# console_handler = logging.StreamHandler(sys.stdout) # Log to standard output
# console_handler.setFormatter(logging.Formatter(log_format)) 
# root_logger.addHandler(console_handler)

# --- End App Logging Setup ---

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter for API endpoints
class RateLimiter:
    def __init__(self, interval_seconds=2):
        self.interval = interval_seconds
        self.last_request_time = {}
        self.lock = threading.Lock()
        
    def allow_request(self, endpoint):
        with self.lock:
            current_time = time.time()
            # Priority endpoints always allowed
            if endpoint in ["/update_params", "/update_message"]:
                return True
                
            # For other endpoints, apply rate limiting
            if endpoint not in self.last_request_time:
                self.last_request_time[endpoint] = current_time
                return True
                
            elapsed = current_time - self.last_request_time[endpoint]
            if elapsed < self.interval:
                return False
                
            self.last_request_time[endpoint] = current_time
            return True


def log_ootb_request(server_url, ootb_request_type, data):
    logging.info(f"OOTB Request: Type={ootb_request_type}, Data={data}")
    # Keep the requests post for now if it serves a specific purpose
    logging_data = {
        "type": ootb_request_type,
        "data": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if not server_url.endswith("/update_ootb_logging"):
        server_logging_url = server_url + "/update_ootb_logging"
    else:
        server_logging_url = server_url
    try:
        requests.post(server_logging_url, json=logging_data, timeout=5)
    except Exception as req_log_e:
        logging.warning(f"Could not log ootb request to server {server_logging_url}: {req_log_e}")


class SharedState:
    def __init__(self, args):
        self.args = args
        # Store all state-related data here
        self.model = args.model
        self.task = getattr(args, 'task', "")
        self.selected_screen = args.selected_screen
        self.user_id = args.user_id
        self.trace_id = args.trace_id
        self.api_keys = args.api_keys
        self.server_url = args.server_url
        self.full_screen_game_mode = getattr(args, 'full_screen_game_mode', 0)
        self.max_steps = getattr(args, 'max_steps', 50)
        
        # Keep minimal state for API responses
        self.chatbot_messages = []
        self.message_queue = []
        
        # Remove loop-related attributes that are no longer needed:
        # - is_processing, should_stop, is_paused (replaced by direct execution)
        # - stop_event, processing_thread (no background processing)
        # - task_updated (not needed for direct execution)
        
        logging.info(f"SharedState initialized for direct execution mode: user={self.user_id}, trace={self.trace_id}")

shared_state = None
rate_limiter = RateLimiter(interval_seconds=2)

# Set up logging for this module
log = logging.getLogger(__name__)

def prepare_environment(state):
    """Dynamically loads and runs preparation logic based on software name."""
    # Determine software name from state (user_id, trace_id, or task)
    software_name = ""
    
    # Check user_id first
    user_id = getattr(state, 'user_id', '').lower()
    task = getattr(state, 'task', '').lower()
    trace_id = getattr(state, 'trace_id', '').lower()
    
    log.info(f"Checking for software in: user_id='{user_id}', trace_id='{trace_id}', task='{task}'")
    
    # Look for known software indicators
    if "star rail" in user_id or "star rail" in trace_id:
        software_name = "star rail"
    elif "powerpoint" in user_id or "powerpoint" in trace_id or "powerpoint" in task:
        software_name = "powerpoint"
    elif "word" in user_id or "word" in trace_id or "word" in task:
        software_name = "word"
    elif "excel" in user_id or "excel" in trace_id or "excel" in task:
        software_name = "excel"
    elif "premiere" in user_id or "premiere" in trace_id or "premiere" in task or \
         "pr" in user_id or "pr" in trace_id or "pr" in task: # Check for 'premiere' or 'pr'
        software_name = "pr" # Module name will be pr_prepare
    # Add more software checks here as needed
    
    # If no specific software found, check task for keywords
    if not software_name:
        log.info("No specific software detected from IDs or task content")
    
    if not software_name:
        log.info("No specific software preparation identified. Skipping preparation.")
        return
    
    log.info(f"Identified software for preparation: '{software_name}'")
    
    # Normalize the software name to be a valid Python module name
    # Replace spaces/hyphens with underscores, convert to lowercase
    module_name_base = software_name.replace(" ", "_").replace("-", "_").lower()
    module_to_run = f"{module_name_base}_prepare"

    log.info(f"Attempting preparation for software: '{software_name}' (Module: '{module_to_run}')")

    try:
        # Construct the full module path within the package
        prep_package = "computer_use_ootb_internal.preparation"
        full_module_path = f"{prep_package}.{module_to_run}"

        # Dynamically import the module
        # Check if module exists first using pkgutil to avoid import errors
        log.debug(f"Looking for preparation module: {full_module_path}")
        loader = pkgutil.find_loader(full_module_path)
        if loader is None:
            log.warning(f"Preparation module '{full_module_path}' not found. Skipping preparation.")
            return

        log.debug(f"Importing preparation module: {full_module_path}")
        prep_module = importlib.import_module(full_module_path)

        # Check if the module has the expected function
        if hasattr(prep_module, "run_preparation") and callable(prep_module.run_preparation):
            log.info(f"Running preparation function from {full_module_path}...")
            prep_module.run_preparation(state)
            log.info(f"Preparation function from {full_module_path} completed.")
        else:
            log.warning(f"Module {full_module_path} found, but does not have a callable 'run_preparation' function. Skipping.")

    except ModuleNotFoundError:
        log.warning(f"Preparation module '{full_module_path}' not found. Skipping preparation.")
    except Exception as e:
        log.error(f"Error during dynamic preparation loading/execution for '{module_to_run}': {e}", exc_info=True)


@app.post("/update_params")
async def update_parameters(request: Request):
    logging.info("Received request to /update_params")
    try:
        data = await request.json()
        
        if 'task' not in data:
            return JSONResponse(
                content={"status": "error", "message": "Missing required field: task"},
                status_code=400
            )
        
        # Clear message histories before updating parameters
        shared_state.message_queue.clear()
        shared_state.chatbot_messages.clear()
        logging.info("Cleared message queue and chatbot messages.")

        shared_state.args = argparse.Namespace(**data)
        
        # Update shared state when parameters change
        shared_state.model = getattr(shared_state.args, 'model', "teach-mode-gpt-4o")
        shared_state.task = getattr(shared_state.args, 'task', "Following the instructions to complete the task.")
        shared_state.selected_screen = getattr(shared_state.args, 'selected_screen', 0)
        shared_state.user_id = getattr(shared_state.args, 'user_id', "hero_cases")
        shared_state.trace_id = getattr(shared_state.args, 'trace_id', "build_scroll_combat")
        shared_state.api_keys = getattr(shared_state.args, 'api_keys', "sk-proj-1234567890")
        shared_state.server_url = getattr(shared_state.args, 'server_url', "http://ec2-44-234-43-86.us-west-2.compute.amazonaws.com")
        shared_state.max_steps = getattr(shared_state.args, 'max_steps', 50)
        shared_state.full_screen_game_mode = getattr(shared_state.args, 'full_screen_game_mode', 0)

        log_ootb_request(shared_state.server_url, "update_params", data)

        # Call the (now dynamic) preparation function here, after parameters are updated
        prepare_environment(shared_state)

        logging.info("Parameters updated successfully.")
        return JSONResponse(
            content={"status": "success", "message": "Parameters updated", "new_args": vars(shared_state.args)},
            status_code=200
        )
    except Exception as e:
        logging.error("Error processing /update_params:", exc_info=True)
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)

@app.post("/update_message")
async def update_message(request: Request):
    data = await request.json()
    
    if 'message' not in data:
        return JSONResponse(
            content={"status": "error", "message": "Missing required field: message"},
            status_code=400
        )
    
    log_ootb_request(shared_state.server_url, "update_message", data)
    
    message = data['message']
    
    # shared_state.chatbot_messages.append({"role": "user", "content": message, "type": "text"})
    shared_state.task = message
    shared_state.args.task = message

    # TODO: adaptively change full_screen_game_mode
    # full_screen_game_mode = data.get('full_screen_game_mode', 0)  # Default to 0 if not provided
    # shared_state.full_screen_game_mode = full_screen_game_mode
    
    return JSONResponse(
        content={"status": "success", "message": "Message received", "task": shared_state.task},
        status_code=200
    )

@app.get("/get_messages")
async def get_messages(request: Request):
    # Apply rate limiting
    if not rate_limiter.allow_request(request.url.path):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again after 2 seconds."},
            status_code=429
        )
    
    # log_ootb_request(shared_state.server_url, "get_messages", {})
    
    # Return all messages in the queue and clear it
    messages = shared_state.message_queue.copy()
    shared_state.message_queue = []
    
    return JSONResponse(
        content={"status": "success", "messages": messages},
        status_code=200
    )

@app.get("/get_screens")
async def get_screens(request: Request):
    # Apply rate limiting
    if not rate_limiter.allow_request(request.url.path):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again after 2 seconds."},
            status_code=429
        )
    
    log_ootb_request(shared_state.server_url, "get_screens", {})
    
    screen_options, primary_index = get_screen_details()
    
    return JSONResponse(
        content={"status": "success", "screens": screen_options, "primary_index": primary_index},
        status_code=200
    )

@app.post("/stop_processing")
async def stop_processing(request: Request):
    # Apply rate limiting
    if not rate_limiter.allow_request(request.url.path):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again after 2 seconds."},
            status_code=429
        )
    
    log_ootb_request(shared_state.server_url, "stop_processing", {})
    
    return JSONResponse(
        content={"status": "error", "message": "Stop processing is not supported in direct execution mode"},
        status_code=400
    )

@app.post("/toggle_pause")
async def toggle_pause(request: Request):
    # Apply rate limiting
    if not rate_limiter.allow_request(request.url.path):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again after 2 seconds."},
            status_code=429
        )
    
    log_ootb_request(shared_state.server_url, "toggle_pause", {})
    
    return JSONResponse(
        content={"status": "error", "message": "Toggle pause is not supported in direct execution mode"},
        status_code=400
    )

@app.get("/status")
async def get_status(request: Request):
    # Apply rate limiting
    if not rate_limiter.allow_request("/status"):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again later."},
            status_code=429
        )
    
    # log_ootb_request(shared_state.server_url, "get_status", {})
    
    return JSONResponse(
        content={
            "status": "success",
            "mode": "direct_execution",
            "ready": True,
            "message": "Server is ready to receive execute_action requests",
            "user_id": shared_state.user_id if shared_state else "unknown",
            "trace_id": shared_state.trace_id if shared_state else "unknown"
        },
        status_code=200
    )

@app.post("/exec_computer_tool")
async def exec_computer_tool(request: Request):
    logging.info("Received request to /exec_computer_tool")
    try:
        data = await request.json()
        
        # Extract parameters from the request
        selected_screen = data.get('selected_screen', 0)
        full_screen_game_mode = data.get('full_screen_game_mode', 0)
        response = data.get('response', {})
        
        logging.info(f"Executing TeachmodeExecutor with: screen={selected_screen}, mode={full_screen_game_mode}, response={response}")
        
        # Create TeachmodeExecutor in a separate process to avoid event loop conflicts
        # Since TeachmodeExecutor uses asyncio.run() internally, we need to run it in a way
        # that doesn't conflict with FastAPI's event loop
        
        def run_executor():
            executor = TeachmodeExecutor(
                selected_screen=selected_screen,
                full_screen_game_mode=full_screen_game_mode
            )
            
            results = []
            try:
                for action_result in executor(response):
                    results.append(action_result)
            except Exception as exec_error:
                logging.error(f"Error executing action: {exec_error}", exc_info=True)
                return {"error": str(exec_error)}
            
            return results
        
        # Execute in a thread pool to avoid blocking the event loop
        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = await asyncio.get_event_loop().run_in_executor(pool, run_executor)
        
        if isinstance(results, dict) and "error" in results:
            return JSONResponse(
                content={"status": "error", "message": results["error"]},
                status_code=500
            )
            
        logging.info(f"Action results: {results}")
        
        return JSONResponse(
            content={"status": "success", "results": results},
            status_code=200
        )
    except Exception as e:
        logging.error("Error processing /exec_computer_tool:", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": f"Internal server error: {str(e)}"},
            status_code=500
        )

@app.post("/execute_action")
async def execute_action(request: Request):
    """
    Direct action execution endpoint. 
    Replaces the sampling loop with immediate action execution.
    """
    # Apply rate limiting for non-priority endpoints
    if not rate_limiter.allow_request("/execute_action"):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again later."},
            status_code=429
        )
    
    logging.info("Received request to /execute_action")
    
    try:
        data = await request.json()
        
        # Extract parameters from the request
        action_data = data.get('action', {})
        selected_screen = data.get('selected_screen', shared_state.selected_screen if shared_state else 0)
        full_screen_game_mode = data.get('full_screen_game_mode', shared_state.full_screen_game_mode if shared_state else 0)
        user_id = data.get('user_id', shared_state.user_id if shared_state else 'unknown')
        trace_id = data.get('trace_id', shared_state.trace_id if shared_state else 'unknown')
        
        logging.info(f"Executing action directly: user_id={user_id}, trace_id={trace_id}, screen={selected_screen}, mode={full_screen_game_mode}")
        logging.info(f"Action data: {action_data}")
        
        # Create TeachmodeExecutor in a separate process to avoid event loop conflicts
        def run_executor():
            executor = TeachmodeExecutor(
                selected_screen=selected_screen,
                full_screen_game_mode=full_screen_game_mode
            )
            
            try:
                # The executor now directly returns a single result dictionary.
                result = executor(action_data)
                logging.info(f"Action executed with result: {result}")
            except Exception as exec_error:
                logging.error(f"Error executing action: {exec_error}", exc_info=True)
                return {"error": str(exec_error)}
            
            return result
        
        # Execute in a thread pool to avoid blocking the event loop
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await asyncio.get_event_loop().run_in_executor(pool, run_executor)
        
        if isinstance(result, dict) and "error" in result:
            return JSONResponse(
                content={"status": "error", "message": result["error"]},
                status_code=500
            )
        
        # Log the successful action execution
        if shared_state and shared_state.server_url:
            log_ootb_request(
                shared_state.server_url, 
                "action_executed", 
                {
                    "user_id": user_id,
                    "trace_id": trace_id,
                    "action": action_data,
                    "result": result
                }
            )
        
        logging.info(f"Action execution completed successfully: {result}")
        
        return JSONResponse(
            content={
                "status": "success", 
                "result": result,
                "message": "Action executed successfully"
            },
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error in execute_action endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/get_screenshot")
async def get_screenshot(request: Request):
    """
    Capture a screenshot of the specified screen and return it as base64-encoded data.
    Query parameters:
    - screen: Screen index to capture (default: 0)
    - resize: Whether to resize the screenshot (default: true)
    - width: Target width for resizing (default: 1920)
    - height: Target height for resizing (default: 1080)
    """
    # Apply rate limiting
    if not rate_limiter.allow_request("/get_screenshot"):
        return JSONResponse(
            content={"status": "error", "message": "Rate limit exceeded. Try again later."},
            status_code=429
        )
    
    logging.info("Received request to /get_screenshot")
    
    try:
        # Get query parameters
        screen_index = int(request.query_params.get('screen', shared_state.selected_screen if shared_state else 0))
        resize = request.query_params.get('resize', 'true').lower() == 'true'
        target_width = int(request.query_params.get('width', 1920))
        target_height = int(request.query_params.get('height', 1080))
        
        logging.info(f"Taking screenshot: screen={screen_index}, resize={resize}, size={target_width}x{target_height}")
        
        # Import the screenshot function
        from computer_use_ootb_internal.computer_use_demo.tools.screen_capture import get_screenshot as capture_screenshot
        
        # Capture screenshot
        screenshot_pil, screenshot_path = capture_screenshot(
            selected_screen=screen_index,
            resize=resize,
            target_width=target_width,
            target_height=target_height
        )
        
        # Convert to base64
        import base64
        with open(screenshot_path, "rb") as image_file:
            screenshot_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Clean up the temporary file
        import os
        try:
            os.remove(screenshot_path)
        except Exception as cleanup_error:
            logging.warning(f"Could not clean up screenshot file {screenshot_path}: {cleanup_error}")
        
        # Log the successful screenshot capture
        if shared_state and shared_state.server_url:
            log_ootb_request(
                shared_state.server_url, 
                "screenshot_captured", 
                {
                    "screen_index": screen_index,
                    "resize": resize,
                    "dimensions": f"{target_width}x{target_height}"
                }
            )
        
        logging.info(f"Screenshot captured successfully for screen {screen_index}")
        
        return JSONResponse(
            content={
                "status": "success",
                "screenshot": screenshot_base64,
                "screen_index": screen_index,
                "dimensions": {
                    "width": target_width if resize else screenshot_pil.width,
                    "height": target_height if resize else screenshot_pil.height
                },
                "message": "Screenshot captured successfully"
            },
            status_code=200
        )
        
    except IndexError as e:
        logging.error(f"Invalid screen index in get_screenshot: {e}")
        return JSONResponse(
            content={"status": "error", "message": f"Invalid screen index: {screen_index}"},
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error in get_screenshot endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

def initialize_direct_execution_mode():
    """
    Initialize the application for direct action execution mode.
    No more sampling loops - just direct API-driven execution.
    """
    global shared_state
    logging.info("Direct execution mode initialized.")
    
    if shared_state:
        # Set up environment if needed
        try:
            prepare_environment(shared_state)
            logging.info("Environment preparation completed.")
        except Exception as e:
            logging.error(f"Error preparing environment: {e}", exc_info=True)
    
    logging.info("Application ready to receive execute_action requests.")

def main():
    # Logging is set up at the top level now
    logging.info("App main() function starting setup.")
    global app, shared_state, rate_limiter # Ensure app is global if needed by uvicorn
    parser = argparse.ArgumentParser()
    # Add arguments, but NOT host and port
    parser.add_argument("--model", type=str, default="teach-mode-gpt-4o", help="Model name")
    parser.add_argument("--task", type=str, default="Following the instructions to complete the task.", help="Initial task description")
    parser.add_argument("--selected_screen", type=int, default=0, help="Selected screen index")
    parser.add_argument("--user_id", type=str, default="hero_cases", help="User ID for the session")
    parser.add_argument("--trace_id", type=str, default="build_scroll_combat", help="Trace ID for the session")
    parser.add_argument("--api_keys", type=str, default="sk-proj-1234567890", help="API keys")
    parser.add_argument("--server_url", type=str, default="http://ec2-44-234-43-86.us-west-2.compute.amazonaws.com", help="Server URL for the session")
    parser.add_argument("--port", type=int, default=0, help="port to use")

    args = parser.parse_args()

    # Validate args or set defaults if needed (keep these)
    if not hasattr(args, 'model'): args.model = "default_model"
    if not hasattr(args, 'task'): args.task = "default_task"
    if not hasattr(args, 'selected_screen'): args.selected_screen = 0
    if not hasattr(args, 'user_id'): args.user_id = "unknown_user"
    if not hasattr(args, 'trace_id'): args.trace_id = "unknown_trace"
    if not hasattr(args, 'api_keys'): args.api_keys = "none"
    if not hasattr(args, 'server_url'): args.server_url = "none"

    shared_state = SharedState(args)
    rate_limiter = RateLimiter(interval_seconds=2) # Re-initialize rate limiter
    logging.info(f"Shared state initialized for user: {args.user_id}")

    # Initialize direct execution mode instead of starting the old loop
    initialize_direct_execution_mode()

    # --- Restore original port calculation logic --- 
    port = 7888 # Default port
    host = "0.0.0.0" # Listen on all interfaces
    
    if platform.system() == "Windows":
        try:
            username = os.environ["USERNAME"].lower()
            logging.info(f"Determining port based on Windows username: {username}")
            if username == "altair":
                port = 14000
            elif username.startswith("guest") and username[5:].isdigit():
                num = int(username[5:])
                if 1 <= num <= 10: # Assuming max 10 guests for this range
                    port = 14000 + num
                else:
                     logging.warning(f"Guest user number {num} out of range (1-10), using default port {port}.")
            else:
                logging.info(f"Username '{username}' doesn't match specific rules, using default port {port}.")
        except Exception as e:
             logging.error(f"Error determining port from username: {e}. Using default port {port}.", exc_info=True)
    else:
         logging.info(f"Not running on Windows, using default port {port}.")
    # --- End of restored port calculation --- 

    if args.port != 0:
        port = args.port

    logging.info(f"Final Host={host}, Port={port}")
    logging.info("Starting FastAPI server in direct execution mode - listening for execute_action requests")

    try:
        logging.info(f"Starting Uvicorn server on {host}:{port}")
        # Use the calculated port and specific host
        uvicorn.run(app, host=host, port=port)
        logging.info("Uvicorn server stopped.")
    except Exception as main_e:
        logging.error("Error in main execution:", exc_info=True)
    finally:
        logging.info("App main() function finished.")

if __name__ == "__main__":
    main()

    # Test log_ootb_request
    log_ootb_request("http://ec2-44-234-43-86.us-west-2.compute.amazonaws.com", "test_request", {"message": "Test message"})