"""
Agent Proxy Handler for Remote Backend Architecture

This handler acts as a proxy between the frontend WebSocket and a remote backend server.
Architecture: frontend --- (websocket) --- jupyter backend (proxy) --- (websocket) --- remote server

The jupyter backend now serves as:
- WebSocket proxy for agent/LLM communication with remote server
- Local tool host for shell execution, cell execution, etc.
- Message router between frontend and remote backend
"""

import asyncio
import json
import os
import ssl
import certifi
import uuid
import websockets
from tornado.websocket import WebSocketHandler
from typing import Optional
import tornado

from .config import handler_registry
from .image_processor import ImageProcessor
from .websocket_tool_executor import WebSocketToolExecutor
from ..utils import build_remote_backend_url
from ..auth.token_handler import get_current_user_token_string


class AIJLAgentProxyHandler(WebSocketHandler):
    """
    WebSocket proxy handler that bridges frontend to remote backend server.
    
    Responsibilities:
    • Accept user messages from frontend and forward to remote backend
    • Handle local tool execution (cell execution, shell commands, etc.) 
    • Route tool results between frontend, local tools, and remote backend
    • Manage WebSocket connections to both frontend and remote backend
    • Handle image processing and temporary files locally
    """

    def initialize(self, **kwargs):
        self.connection_id: str = str(uuid.uuid4())
        self.current_request_id: str | None = None

        # Frontend WebSocket connection state
        self._is_closed = False
        self.waiter: asyncio.Future | None = None
        
        # Remote backend connection
        self.remote_websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.remote_url = build_remote_backend_url("agent")
        self._remote_connection_lock = asyncio.Lock()
        
        # Server base URL for API calls
        self.server_url = os.environ.get("SERVER_URL", "http://localhost:8888")
        
        # Token-based authentication (replaces access key system)
        print("[PROXY] Token authentication enabled - will forward tokens to remote backend")
        
        # Initialize local components (for tool execution)
        self.image_processor = ImageProcessor(self.connection_id, self.server_url)
        self.tool_executor = WebSocketToolExecutor(self)

        # Track pending frontend requests for agent mode detection
        self._pending_frontend_requests = set()
        
        # Register this handler globally
        handler_registry[self.connection_id] = self

    def _get_user_token(self) -> Optional[str]:
        """
        Get user token from local file (saved during OAuth flow).
        
        Returns:
            User token if found, None otherwise
        """
        # Use existing token handler utility
        token = get_current_user_token_string()
        if token:
            print(f"[PROXY] ✅ Found user token (length: {len(token)})")
        else:
            print("[PROXY] ❌ No user token found")
        return token

    def _is_remote_connection_closed(self) -> bool:
        """Check if the remote WebSocket connection is closed."""
        if self.remote_websocket is None:
            return True
        
        try:
            # Check if the connection is closed
            # For websockets library, use the state property
            from websockets.protocol import State
            return self.remote_websocket.state != State.OPEN
        except Exception as e:
            print(f"[PROXY] Error checking connection state: {e}")
            # If we can't determine the state, assume it's open to avoid reconnecting unnecessarily
            return False

    def check_origin(self, origin: str) -> bool:
        # NOTE: relax CORS – adjust for production
        return True

    async def open(self):
        """Handle WebSocket connection opening from frontend."""
        # Get user token from local file
        user_token = self._get_user_token()
        
        if not user_token:
            print("[PROXY] ❌ No authentication token available")
            await self._safe_write_message({
                "type": "system",
                "msg": "error", 
                "error": "Authentication required. Please log in to use this service."
            })
            return
        
        # Store token for remote backend connection
        self.user_token = user_token
        
        # Tell the frontend we are ready
        await self._safe_write_message({
            "type": "system", 
            "msg": "ready", 
            "connection_id": self.connection_id
        })
        
        # Establish connection to remote backend
        await self._connect_to_remote_backend()

    async def _connect_to_remote_backend(self):
        """Establish WebSocket connection to remote backend server."""
        try:
            async with self._remote_connection_lock:
                if self.remote_websocket is None or self._is_remote_connection_closed():
                    # Add user token to URL for authentication
                    connection_url = self.remote_url
                    if hasattr(self, 'user_token') and self.user_token:
                        separator = "&" if "?" in connection_url else "?"
                        connection_url = f"{connection_url}{separator}token={self.user_token}"
                        print(f"[PROXY] Connecting to remote backend with user authentication: {self.remote_url}")
                    else:
                        print(f"[PROXY] Connecting to remote backend without authentication: {self.remote_url}")
                    
                    # Create SSL context for WebSocket connection
                    try:
                        ssl_context = ssl.create_default_context(cafile=certifi.where())
                        print(f"[PROXY] Using certifi certificate bundle for WebSocket SSL verification")
                    except Exception as e:
                        print(f"[PROXY] Failed to create SSL context with certifi: {e}")
                        # Fallback to default SSL context
                        ssl_context = ssl.create_default_context()
                    
                    self.remote_websocket = await websockets.connect(connection_url, ssl=ssl_context)
                    
                    # Start listening for messages from remote backend
                    asyncio.create_task(self._listen_to_remote_backend())
                    
                    print(f"[PROXY] Connected to remote backend successfully")
        except Exception as e:
            print(f"[PROXY] Failed to connect to remote backend: {e}")
            await self._safe_write_message({
                "type": "system",
                "msg": "error", 
                "error": f"Failed to connect to remote backend: {e}"
            })

    async def _listen_to_remote_backend(self):
        """Listen for messages from remote backend and forward to frontend."""
        try:
            async for message in self.remote_websocket:
                try:
                    data = json.loads(message)
                    await self._handle_remote_backend_message(data)
                except json.JSONDecodeError as e:
                    print(f"[PROXY] Invalid JSON from remote backend: {e}")
                except Exception as e:
                    print(f"[PROXY] Error handling remote backend message: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("[PROXY] Remote backend connection closed")
        except Exception as e:
            print(f"[PROXY] Error listening to remote backend: {e}")

    async def _handle_remote_backend_message(self, data):
        """Handle messages from remote backend."""
        msg_type = data.get("type")
        print(f"[PROXY] Received message from remote backend: {msg_type}")
        
        if msg_type in ["assistant_chunk", "assistant_complete", "system", "tool_call", "tool_call_output"]:
            # Forward AI responses directly to frontend
            print(f"[PROXY] Forwarding {msg_type} to frontend")
            await self._safe_write_message(data)
            
        elif msg_type == "tool_call_request":
            # Handle tool call request from remote backend
            print(f"[PROXY] Handling tool call request: {data.get('tool_name')}")
            await self._handle_tool_call_request(data)
            
        elif msg_type == "shell_execute":
            # Handle shell execute as local tool execution (not frontend request)
            print(f"[PROXY] Handling shell execute as local tool")
            await self._handle_shell_execute_locally(data)
            
        elif msg_type in ["cell_execute", "rerun_all_cells", "edit_cell", "insert_markdown_cell", 
                         "shell_permission_request", "rerun_all_cells_permission_request"]:
            # Handle frontend request messages from remote backend
            print(f"[PROXY] Forwarding frontend request {msg_type} to frontend")
            await self._safe_write_message(data)
            
        else:
            # Forward other messages to frontend
            print(f"[PROXY] Forwarding unknown message type {msg_type} to frontend")
            await self._safe_write_message(data)

    async def _handle_shell_execute_locally(self, data):
        """Handle shell execute request from remote backend by executing locally on proxy server."""
        try:
            command = data.get("command", "")
            request_id = data.get("request_id")
            
            print(f"[PROXY] Executing shell command locally: {command}")
            
            # Execute shell command using proxy's tool executor
            result = await self.tool_executor.shell_execute(command)
            
            # Send result back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": request_id,
                "result": result
            })
            
        except Exception as e:
            print(f"[PROXY] Error executing shell command: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": data.get("request_id"),
                "result": f"Error executing shell command: {e}"
            })

    async def _check_agent_mode_timeout(self, request_id: str, tool_name: str):
        """Check if we're in agent mode by timing out on cell_execute requests."""
        await asyncio.sleep(10)  # Wait 10 seconds
        
        # If the request_id is still tracked, it means no response came back
        # This indicates agent mode where frontend doesn't properly handle cell_execute
        if hasattr(self, '_pending_frontend_requests') and request_id in self._pending_frontend_requests:
            print(f"[PROXY] Detected agent mode - frontend didn't respond to {tool_name} in 10 seconds")
            
            # Send error response
            error_result = "Error: cell_execute requires a connected frontend with a Jupyter kernel. In agent mode, please use shell_execute for command-line operations instead."
            
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": request_id,
                "tool_name": tool_name,
                "result": error_result
            })
            
            # Clean up the pending request
            self._pending_frontend_requests.discard(request_id)

    async def _handle_tool_call_request(self, data):
        """Handle tool call request from remote backend by executing locally."""
        try:
            tool_name = data.get("tool_name")
            tool_args = data.get("tool_args", {})
            request_id = data.get("request_id")
            
            print(f"[PROXY] Handling tool call request: {tool_name} with args: {tool_args}")
            
            # Check if this is a frontend-interactive tool
            frontend_interactive_tools = ["edit_cell", "rerun_all_cells", "insert_markdown_cell", "cell_execute"]
            
            if tool_name in frontend_interactive_tools:
                print(f"[PROXY] Forwarding frontend-interactive tool {tool_name} to frontend with request_id: {request_id}")
                # Forward frontend-interactive tools directly to frontend
                frontend_message = {
                    "type": tool_name,
                    "request_id": request_id,
                    "connection_id": self.connection_id,
                    **tool_args  # Spread the tool arguments into the message
                }
                print(f"[PROXY] Frontend message: {frontend_message}")
                
                # Try to send to frontend, but handle special cases
                success = await self._safe_write_message(frontend_message)
                if success:
                    print(f"[PROXY] Frontend message sent. Waiting for response...")
                    
                    # For cell_execute in agent mode, add a timeout check
                    # since agent mode frontend may not respond properly to cell_execute
                    if tool_name == "cell_execute":
                        # Track this request and start a timeout timer
                        self._pending_frontend_requests.add(request_id)
                        asyncio.create_task(self._check_agent_mode_timeout(request_id, tool_name))
                    
                    # The result should come back via _handle_local_tool_result and be forwarded to remote backend
                else:
                    # No frontend connected - handle locally or return error
                    print(f"[PROXY] No frontend connected for {tool_name}, handling locally")
                    if tool_name == "cell_execute":
                        # For cell_execute, return an informative error
                        error_result = "Error: cell_execute requires a connected frontend with a Jupyter kernel. In agent mode, please use shell_execute for command-line operations instead."
                    else:
                        error_result = f"Error: {tool_name} requires a connected frontend with a Jupyter notebook."
                    
                    # Send error result back to remote backend
                    await self._send_to_remote_backend({
                        "type": "tool_call_result",
                        "request_id": request_id,
                        "tool_name": tool_name,
                        "result": error_result
                    })
                
            else:
                print(f"[PROXY] Executing local tool: {tool_name}")
                # Execute non-interactive tools locally
                result = await self._execute_local_tool(tool_name, tool_args, request_id)
                
                # Send result back to remote backend
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "result": result
                })
            
        except Exception as e:
            print(f"[PROXY] Error handling tool call request: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": data.get("request_id"),
                "tool_name": data.get("tool_name"),
                "result": f"Error executing tool: {e}"
            })

    async def _execute_local_tool(self, tool_name: str, tool_args: dict, request_id: str = None) -> str:
        """Execute a tool locally using the WebSocket tool executor."""
        if tool_name == "cell_execute":
            return await self.tool_executor.cell_execute(tool_args.get("code", ""))
            
        elif tool_name == "shell_execute":
            return await self.tool_executor.shell_execute(tool_args.get("command", ""))
            
        elif tool_name == "edit_cell":
            return await self.tool_executor.edit_cell(
                tool_args.get("cell_index", 0),
                tool_args.get("code", ""),
                tool_args.get("rerun", False),
                request_id
            )
            
        elif tool_name == "rerun_all_cells":
            return await self.tool_executor.rerun_all_cells(request_id)
            

            
        elif tool_name == "insert_markdown_cell": 
            return await self.tool_executor.insert_markdown_cell(
                tool_args.get("cell_index", 0),
                tool_args.get("content", ""),
                request_id
            )
            
        elif tool_name == "read_file":
            return await self.tool_executor.read_file(
                tool_args.get("file_path", ""),
                tool_args.get("start_row_index", 0),
                tool_args.get("end_row_index", 200)
            )
            
        elif tool_name == "interpret_image":
            return "Error: interpret_image tool should be handled by the remote backend, not the proxy"
            
        else:
            return f"Unknown tool: {tool_name}"

    async def _send_to_remote_backend(self, data):
        """Send message to remote backend."""
        try:
            if self.remote_websocket and not self._is_remote_connection_closed():
                await self.remote_websocket.send(json.dumps(data))
            else:
                await self._connect_to_remote_backend()
                if self.remote_websocket and not self._is_remote_connection_closed():
                    await self.remote_websocket.send(json.dumps(data))
        except Exception as e:
            print(f"[PROXY] Error sending to remote backend: {e}")
            import traceback
            traceback.print_exc()

    async def _safe_write_message(self, data):
        """Safely write a message to the frontend WebSocket with error handling."""
        if self._is_closed:
            return False
        
        try:
            await self.write_message(json.dumps(data))
            return True
        except tornado.websocket.WebSocketClosedError:
            self._is_closed = True
            return False
        except Exception as e:
            print(f"Error writing to frontend WebSocket: {str(e)}")
            return False

    async def on_message(self, raw: str):
        """
        Handle incoming WebSocket messages from frontend.
        Route appropriately between local tools and remote backend.
        """
        try:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "user":
                # Forward user messages to remote backend for AI processing
                await self._forward_to_remote_backend(msg)

            elif msg_type == "cancel":
                # Forward cancellation to remote backend
                await self._forward_to_remote_backend(msg)
                
            elif msg_type in ["cell_result", "shell_permission_response", "rerun_all_cells_result", 
                             "edit_cell_result", "insert_markdown_cell_result", "rerun_all_cells_permission_response"]:
                # Handle local tool results
                await self._handle_local_tool_result(msg)
                
            else:
                # Forward other message types to remote backend
                await self._forward_to_remote_backend(msg)

        except Exception as e:
            print(f"Error in on_message: {e}")
            import traceback
            traceback.print_exc()

    async def _forward_to_remote_backend(self, msg):
        """Forward message to remote backend."""
        # Add connection ID for routing
        msg["connection_id"] = self.connection_id
        
        # Ensure connection to remote backend
        if not self.remote_websocket or self._is_remote_connection_closed():
            await self._connect_to_remote_backend()
        
        await self._send_to_remote_backend(msg)

    async def _handle_local_tool_result(self, msg):
        """Handle results from local tool execution (from frontend)."""
        msg_type = msg.get("type")
        conn_id = msg.get("connection_id", self.connection_id)
        
        # Locate the correct handler
        handler = handler_registry.get(conn_id, self)
        
        if msg_type == "cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            if request_id:
                # This is from a remote backend tool call, forward it back
                print(f"[PROXY] Forwarding cell_result to remote backend with request_id: {request_id}")
                
                # Clean up pending request tracking
                if hasattr(self, '_pending_frontend_requests'):
                    self._pending_frontend_requests.discard(request_id)
                
                # Process the result to check for image data
                if '"image/png"' in result:
                    print(f"[PROXY] Detected image/png data in cell_result")
                    modified_result = await handler.image_processor.replace_base64_with_urls(result)
                    result = modified_result
                
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "cell_execute",
                    "result": result
                })
            else:
                # Process the result to check for image data (local execution)
                await self._process_cell_result(handler, result)
            
        elif msg_type == "edit_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            # Process the result to check for image data
            if '"image/png"' in result:
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                result = modified_result
            
            # Always forward the result back to remote backend with request_id
            if request_id:
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "edit_cell",
                    "result": result
                })
            else:
                # Fallback: treat as local tool execution result
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
            
        elif msg_type == "shell_permission_response":
            allowed = msg.get("allowed", False) 
            request_id = msg.get("request_id")
            print(f"[PROXY] Received shell permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[PROXY] Cannot set shell permission response - waiter not available")
                
        elif msg_type == "rerun_all_cells_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            # If this result is from a remote backend tool call, forward it back
            if request_id:
                print(f"[PROXY] Forwarding rerun_all_cells_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "rerun_all_cells",
                    "result": result
                })
            else:
                # Set the result directly to the waiter (for local calls)
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for {msg_type}")
                
        elif msg_type == "insert_markdown_cell_result":
            success = msg.get("success", False)
            request_id = msg.get("request_id")
            
            if success:
                result = msg.get("message", "Markdown cell inserted successfully")
            else:
                error = msg.get("error", "Unknown error occurred")
                result = f"Error inserting markdown cell: {error}"
            
            # If this result is from a remote backend tool call, forward it back
            if request_id:
                print(f"[PROXY] Forwarding insert_markdown_cell_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "insert_markdown_cell",
                    "result": result
                })
            else:
                # Set the result directly to the waiter (for local calls)
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for insert markdown cell result")
                
        elif msg_type == "rerun_all_cells_permission_response":
            allowed = msg.get("allowed", False)
            request_id = msg.get("request_id")
            print(f"[PROXY] Received rerun permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[PROXY] Cannot set rerun permission response - waiter not available")

    async def _process_cell_result(self, handler, result):
        """Process cell results and handle image data conversion for display."""
        try:
            print(f"[PROXY] Processing cell result of length: {len(result) if result else 0}")
            
            # Check if result contains image data that needs to be converted to URLs
            if '"image/png"' in result:
                print(f"[PROXY] Detected image/png data in cell result")
                # Replace base64 data with URLs in the result
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                
                # Set the modified result to unblock the function call
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(modified_result)
                else:
                    print(f"[PROXY] Handler waiter not available or already done")
            else:
                # No image, just set the result directly
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available or already done")
                    
        except Exception as e:
            print(f"[PROXY] Error processing cell result: {e}")
            import traceback
            traceback.print_exc()
            # Fail safely by returning the original result
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)

    def on_close(self):
        """Handle WebSocket connection closing."""
        # Set closed flag
        self._is_closed = True
        
        # Close remote backend connection
        if self.remote_websocket and not self._is_remote_connection_closed():
            asyncio.create_task(self.remote_websocket.close())
        
        # Deregister and clean up
        handler_registry.pop(self.connection_id, None)
        if self.waiter and not self.waiter.done():
            self.waiter.cancel()
        self.waiter = None
        
        # Clean up image processor
        self.image_processor.cleanup_images() 