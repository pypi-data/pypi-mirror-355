"""WebSocket server wrapper for Claude Code SDK with enhanced capabilities."""

import asyncio
import json
import logging
import webbrowser
from typing import AsyncGenerator, Dict, Any, Optional, Set, List
from dataclasses import asdict
from pathlib import Path
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

from claude_max import query, ClaudeCodeOptions
from claude_max.types import (
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock
)
from claude_max.auth_config import ClaudeCodeOAuthConfig
from claude_max.oauth_flow import ClaudeCodeOAuthFlow
from claude_max.auth import TokenStorage, AuthToken

# Add agent_system to path if it exists
agent_system_path = Path(__file__).parent.parent.parent / "agent_system"
if agent_system_path.exists():
    sys.path.insert(0, str(agent_system_path.parent))
    try:
        from agent_system.integrations.tool_registry_client import ToolRegistryClient
        TOOL_REGISTRY_AVAILABLE = True
    except ImportError:
        TOOL_REGISTRY_AVAILABLE = False
else:
    TOOL_REGISTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConversationSession:
    """Manages a conversation session with Claude."""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.query_task: Optional[asyncio.Task] = None
        self.interrupt_event = asyncio.Event()
        self.is_active = True
        self.message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.options: Optional[ClaudeCodeOptions] = None
        # OAuth support
        self.oauth_flow: Optional[ClaudeCodeOAuthFlow] = None
        self.auth_token: Optional[AuthToken] = None
        self.oauth_state: Optional[str] = None
        self.is_authenticated = False


class EnhancedClaudeWebSocketServer:
    """Enhanced WebSocket server for real-time Claude Code interactions."""
    
    def __init__(self, app: Optional[FastAPI] = None, enable_oauth: bool = True):
        self.app = app or FastAPI()
        self.enable_oauth = enable_oauth
        self._setup_routes()
        self.sessions: Dict[str, ConversationSession] = {}
        self.tool_registry_client: Optional[ToolRegistryClient] = None
        
        # OAuth configuration
        if enable_oauth:
            self.oauth_config = ClaudeCodeOAuthConfig.for_claude_code_max()
            self.token_storage = TokenStorage()
        
        # Initialize tool registry client if available
        if TOOL_REGISTRY_AVAILABLE:
            self.tool_registry_client = ToolRegistryClient()
        
    def _setup_routes(self):
        """Set up WebSocket and HTTP routes."""
        
        @self.app.get("/")
        async def get():
            """Serve the HTML UI."""
            if self.enable_oauth:
                return HTMLResponse(content=self._generate_oauth_ui())
            else:
                ui_path = Path("claude_ui.html")
                if not ui_path.exists():
                    ui_path = Path(__file__).parent.parent.parent / "claude_ui.html"
                
                if ui_path.exists():
                    with open(ui_path, "r") as f:
                        return HTMLResponse(content=f.read())
                else:
                    return HTMLResponse(content="<h1>UI file not found</h1>")
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Handle WebSocket connections."""
            await self._handle_websocket(websocket)
        
        # OAuth routes
        if self.enable_oauth:
            @self.app.get("/oauth/login/{session_id}")
            async def oauth_login(session_id: str):
                """Initiate OAuth login for a WebSocket session."""
                return await self._handle_oauth_login(session_id)
            
            @self.app.get("/oauth/callback")
            async def oauth_callback(request: Request):
                """Handle OAuth callback."""
                return await self._handle_oauth_callback(request)
            
            @self.app.get("/oauth/status/{session_id}")
            async def oauth_status(session_id: str):
                """Get OAuth status for a session."""
                return await self._handle_oauth_status(session_id)
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle a WebSocket connection."""
        await websocket.accept()
        session_id = f"session_{id(websocket)}"
        session = ConversationSession(session_id, websocket)
        self.sessions[session_id] = session
        
        # Check for existing OAuth token
        if self.enable_oauth:
            existing_token = self.token_storage.load_token()
            if existing_token and not existing_token.is_expired():
                session.auth_token = existing_token
                session.is_authenticated = True
        
        # Send connection success with capabilities
        capabilities = {
            "concurrent_input": True,
            "tool_definition": TOOL_REGISTRY_AVAILABLE,
            "interrupt_query": True
        }
        
        if self.enable_oauth:
            capabilities["oauth_authentication"] = True
            capabilities["token_refresh"] = True
        
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "oauth_enabled": self.enable_oauth,
                "authenticated": session.is_authenticated if self.enable_oauth else None,
                "oauth_login_url": f"/oauth/login/{session_id}" if self.enable_oauth else None,
                "capabilities": capabilities
            }
        })
        
        try:
            # Start message processor
            processor_task = asyncio.create_task(self._process_messages(session))
            
            while session.is_active:
                # Receive message from client
                try:
                    data = await websocket.receive_json()
                    await session.message_queue.put(data)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            # Cleanup
            session.is_active = False
            processor_task.cancel()
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            session.is_active = False
            if session.query_task and not session.query_task.done():
                session.query_task.cancel()
            del self.sessions[session_id]
            try:
                await websocket.close()
            except:
                pass
    
    async def _process_messages(self, session: ConversationSession):
        """Process messages from the client queue."""
        while session.is_active:
            try:
                # Get message with timeout to allow periodic checks
                data = await asyncio.wait_for(session.message_queue.get(), timeout=1.0)
                
                message_type = data.get("type")
                
                if message_type == "query":
                    await self._handle_query(session, data)
                elif message_type == "input":
                    await self._handle_input(session, data)
                elif message_type == "interrupt":
                    await self._handle_interrupt(session)
                elif message_type == "define_tool":
                    await self._handle_define_tool(session, data)
                elif message_type == "get_tools":
                    await self._handle_get_tools(session, data)
                elif message_type == "ping":
                    await session.websocket.send_json({"type": "pong"})
                # OAuth message types
                elif message_type == "oauth_login":
                    await self._handle_oauth_login_request(session, data)
                elif message_type == "oauth_logout":
                    await self._handle_oauth_logout(session)
                elif message_type == "oauth_refresh":
                    await self._handle_oauth_refresh(session)
                elif message_type == "oauth_status":
                    await self._handle_oauth_status_request(session)
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await session.websocket.send_json({
                    "type": "error",
                    "data": {"error": str(e)}
                })
    
    async def _handle_query(self, session: ConversationSession, data: Dict[str, Any]):
        """Handle a query request from the client."""
        if session.query_task and not session.query_task.done():
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": "A query is already in progress. Use interrupt to stop it."}
            })
            return
        
        # Check OAuth authentication if enabled
        if self.enable_oauth:
            if not session.is_authenticated:
                await session.websocket.send_json({
                    "type": "auth_required",
                    "data": {
                        "message": "Authentication required to make queries",
                        "oauth_login_url": f"/oauth/login/{session.session_id}"
                    }
                })
                return
            
            # Check token expiry and auto-refresh if possible
            if session.auth_token and session.auth_token.is_expired():
                if session.auth_token.refresh_token:
                    try:
                        await self._refresh_session_token(session)
                    except Exception as e:
                        logger.error(f"Auto-refresh failed: {e}")
                        await session.websocket.send_json({
                            "type": "auth_expired",
                            "data": {
                                "message": "Authentication expired, please login again",
                                "oauth_login_url": f"/oauth/login/{session.session_id}"
                            }
                        })
                        return
                else:
                    await session.websocket.send_json({
                        "type": "auth_expired",
                        "data": {
                            "message": "Authentication expired, please login again",
                            "oauth_login_url": f"/oauth/login/{session.session_id}"
                        }
                    })
                    return
        
        prompt = data.get("prompt", "")
        options_data = data.get("options", {})
        
        # Build ClaudeCodeOptions from client data
        session.options = ClaudeCodeOptions(
            allowed_tools=options_data.get("allowed_tools", []),
            permission_mode=options_data.get("permission_mode", "default"),
            max_thinking_tokens=options_data.get("max_thinking_tokens", 8000),
            model=options_data.get("model"),
            cwd=options_data.get("cwd"),
            continue_conversation=options_data.get("continue_conversation", False),
            resume=options_data.get("resume")
        )
        
        # Reset interrupt event
        session.interrupt_event.clear()
        
        # Create query task
        session.query_task = asyncio.create_task(
            self._run_query(session, prompt)
        )
    
    async def _run_query(self, session: ConversationSession, prompt: str):
        """Run a query with Claude."""
        try:
            # Send start message
            await session.websocket.send_json({
                "type": "query_start",
                "data": {"prompt": prompt}
            })
            
            # Stream responses from Claude
            async for message in query(prompt=prompt, options=session.options):
                # Check for interrupt
                if session.interrupt_event.is_set():
                    await session.websocket.send_json({
                        "type": "query_interrupted"
                    })
                    break
                
                await self._send_message(session.websocket, message)
            
            # Send end message
            await session.websocket.send_json({
                "type": "query_end"
            })
            
        except asyncio.CancelledError:
            await session.websocket.send_json({
                "type": "query_cancelled"
            })
        except Exception as e:
            logger.error(f"Query error: {e}")
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": str(e)}
            })
    
    async def _handle_input(self, session: ConversationSession, data: Dict[str, Any]):
        """Handle user input during a query."""
        input_text = data.get("text", "")
        
        # For now, we'll just acknowledge the input
        # In a real implementation, this would be passed to the running query
        await session.websocket.send_json({
            "type": "input_acknowledged",
            "data": {"text": input_text}
        })
        
        # TODO: Implement actual input handling to the running query
        # This would require modifying the SDK to support interactive input
    
    async def _handle_interrupt(self, session: ConversationSession):
        """Handle query interruption."""
        if session.query_task and not session.query_task.done():
            session.interrupt_event.set()
            session.query_task.cancel()
            await session.websocket.send_json({
                "type": "interrupt_acknowledged"
            })
    
    async def _handle_define_tool(self, session: ConversationSession, data: Dict[str, Any]):
        """Handle tool definition request."""
        if not TOOL_REGISTRY_AVAILABLE:
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": "Tool registry not available"}
            })
            return
        
        tool_data = data.get("tool", {})
        agent_id = data.get("agent_id", session.session_id)
        
        try:
            # Create tool in registry
            result = await self.tool_registry_client.create_tool(tool_data, agent_id)
            
            await session.websocket.send_json({
                "type": "tool_defined",
                "data": {
                    "tool_id": result.get("id"),
                    "tool_name": result.get("name"),
                    "status": "success",
                    "details": result
                }
            })
        except Exception as e:
            logger.error(f"Tool definition error: {e}")
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": f"Failed to define tool: {str(e)}"}
            })
    
    async def _handle_get_tools(self, session: ConversationSession, data: Dict[str, Any]):
        """Handle request to get available tools."""
        if not TOOL_REGISTRY_AVAILABLE:
            await session.websocket.send_json({
                "type": "tools_list",
                "data": {"tools": [], "source": "default"}
            })
            return
        
        try:
            # Get tools from registry
            tools = await self.tool_registry_client.get_tools(
                name=data.get("name"),
                limit=data.get("limit", 100)
            )
            
            await session.websocket.send_json({
                "type": "tools_list",
                "data": {"tools": tools, "source": "registry"}
            })
        except Exception as e:
            logger.error(f"Get tools error: {e}")
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": f"Failed to get tools: {str(e)}"}
            })
    
    async def _send_message(self, websocket: WebSocket, message):
        """Send a Claude message to the WebSocket client."""
        if isinstance(message, AssistantMessage):
            # Convert content blocks to serializable format
            content_data = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    content_data.append({
                        "type": "text",
                        "text": block.text
                    })
                elif isinstance(block, ToolUseBlock):
                    content_data.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                elif isinstance(block, ToolResultBlock):
                    content_data.append({
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                        "is_error": block.is_error
                    })
            
            await websocket.send_json({
                "type": "assistant_message",
                "data": {"content": content_data}
            })
            
        elif isinstance(message, SystemMessage):
            await websocket.send_json({
                "type": "system_message",
                "data": {
                    "subtype": message.subtype,
                    **message.data
                }
            })
            
        elif isinstance(message, ResultMessage):
            await websocket.send_json({
                "type": "result_message",
                "data": {
                    "subtype": message.subtype,
                    "cost_usd": message.cost_usd,
                    "duration_ms": message.duration_ms,
                    "session_id": message.session_id,
                    "total_cost_usd": message.total_cost_usd,
                    "num_turns": message.num_turns,
                    "usage": message.usage
                }
            })
    
    # OAuth handler methods
    async def _handle_oauth_login(self, session_id: str):
        """Handle OAuth login initiation."""
        if session_id not in self.sessions:
            return HTMLResponse(
                content="<h1>Invalid session</h1>",
                status_code=400
            )
        
        session = self.sessions[session_id]
        
        # Create OAuth flow
        session.oauth_flow = ClaudeCodeOAuthFlow(
            self.oauth_config,
            self.token_storage
        )
        
        async with session.oauth_flow as flow:
            # Start callback server
            await flow.start_callback_server()
            
            # Generate auth URL
            auth_url = self.oauth_config.get_authorize_url(
                state=flow.session.state if flow.session else None,
                code_challenge=flow.session.challenge if flow.session and self.oauth_config.use_pkce else None
            )
            
            # Store OAuth state
            session.oauth_state = flow.session.state if flow.session else None
            
            # Notify WebSocket client
            await session.websocket.send_json({
                "type": "oauth_login_initiated",
                "data": {
                    "auth_url": auth_url,
                    "message": "Please complete authentication in the opened browser window"
                }
            })
            
            return RedirectResponse(url=auth_url)
    
    async def _handle_oauth_callback(self, request: Request):
        """Handle OAuth callback."""
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        if error:
            return HTMLResponse(
                content=f"<h1>OAuth Error</h1><p>{error}</p>",
                status_code=400
            )
        
        # Find session by state
        session = None
        for s in self.sessions.values():
            if s.oauth_state == state:
                session = s
                break
        
        if not session:
            return HTMLResponse(
                content="<h1>Invalid OAuth state</h1>",
                status_code=400
            )
        
        try:
            if session.oauth_flow:
                async with session.oauth_flow as flow:
                    # Wait for callback to be processed
                    token = await flow._wait_for_callback()
                    
                    # Exchange code for token
                    auth_token = await flow._exchange_code_for_token(token)
                    
                    # Store token
                    session.auth_token = auth_token
                    session.is_authenticated = True
                    
                    # Save to storage
                    self.token_storage.save_token(auth_token)
                    
                    # Notify WebSocket client
                    await session.websocket.send_json({
                        "type": "oauth_success",
                        "data": {
                            "message": "Authentication successful!",
                            "token_type": auth_token.token_type,
                            "expires_at": auth_token.expires_at.isoformat() if auth_token.expires_at else None,
                            "scopes": auth_token.scope
                        }
                    })
                    
                    return HTMLResponse(content=self._generate_oauth_success_page())
        
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            
            await session.websocket.send_json({
                "type": "oauth_error",
                "data": {
                    "error": str(e),
                    "message": "Authentication failed"
                }
            })
            
            return HTMLResponse(
                content=f"<h1>Authentication Failed</h1><p>{str(e)}</p>",
                status_code=400
            )
    
    async def _handle_oauth_status(self, session_id: str):
        """Get OAuth status for a session."""
        if session_id not in self.sessions:
            return {"authenticated": False, "error": "Invalid session"}
        
        session = self.sessions[session_id]
        return {
            "authenticated": session.is_authenticated,
            "token_expires": session.auth_token.expires_at.isoformat() if session.auth_token and session.auth_token.expires_at else None
        }
    
    async def _handle_oauth_login_request(self, session: ConversationSession, data: Dict[str, Any]):
        """Handle OAuth login request from WebSocket."""
        if not self.enable_oauth:
            await session.websocket.send_json({
                "type": "error",
                "data": {"error": "OAuth not enabled"}
            })
            return
        
        login_url = f"http://localhost:8000/oauth/login/{session.session_id}"
        await session.websocket.send_json({
            "type": "oauth_login_url",
            "data": {
                "url": login_url,
                "message": "Click the link or visit the URL to authenticate"
            }
        })
        
        # Optionally open browser automatically
        if data.get("auto_open", True):
            webbrowser.open(login_url)
    
    async def _handle_oauth_logout(self, session: ConversationSession):
        """Handle OAuth logout request."""
        if not self.enable_oauth:
            return
        
        # Revoke token if possible
        if session.auth_token and session.oauth_flow:
            try:
                async with session.oauth_flow as flow:
                    await flow.revoke_token(session.auth_token.access_token)
            except Exception as e:
                logger.error(f"Token revocation error: {e}")
        
        # Clear token
        session.auth_token = None
        session.is_authenticated = False
        self.token_storage.clear_token()
        
        await session.websocket.send_json({
            "type": "oauth_logout_success",
            "data": {"message": "Logged out successfully"}
        })
    
    async def _handle_oauth_refresh(self, session: ConversationSession):
        """Handle OAuth token refresh request."""
        if not self.enable_oauth or not session.auth_token or not session.auth_token.refresh_token:
            await session.websocket.send_json({
                "type": "oauth_refresh_error",
                "data": {"error": "No refresh token available"}
            })
            return
        
        try:
            await self._refresh_session_token(session)
            await session.websocket.send_json({
                "type": "oauth_refresh_success",
                "data": {
                    "message": "Token refreshed successfully",
                    "expires_at": session.auth_token.expires_at.isoformat() if session.auth_token.expires_at else None
                }
            })
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            await session.websocket.send_json({
                "type": "oauth_refresh_error",
                "data": {"error": str(e)}
            })
    
    async def _handle_oauth_status_request(self, session: ConversationSession):
        """Handle OAuth status request from WebSocket."""
        await session.websocket.send_json({
            "type": "oauth_status",
            "data": {
                "authenticated": session.is_authenticated,
                "token_expires": session.auth_token.expires_at.isoformat() if session.auth_token and session.auth_token.expires_at else None,
                "token_type": session.auth_token.token_type if session.auth_token else None,
                "scopes": session.auth_token.scope if session.auth_token else None
            }
        })
    
    async def _refresh_session_token(self, session: ConversationSession):
        """Refresh the session's OAuth token."""
        if not session.oauth_flow:
            session.oauth_flow = ClaudeCodeOAuthFlow(
                self.oauth_config,
                self.token_storage
            )
        
        async with session.oauth_flow as flow:
            new_token = await flow.refresh_token(session.auth_token.refresh_token)
            session.auth_token = new_token
    
    def _generate_oauth_success_page(self) -> str:
        """Generate OAuth success page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 400px;
                }
                .success { color: #22c55e; }
                .spinner {
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #3b82f6;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            <script>
                setTimeout(() => {
                    window.close();
                }, 3000);
            </script>
        </head>
        <body>
            <div class="container">
                <div style="font-size: 48px; margin-bottom: 20px;">🎉</div>
                <h1>Authentication Successful!</h1>
                <p class="success">You can now use Claude Code with OAuth authentication.</p>
                <div class="spinner"></div>
                <p>This window will close automatically...</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_oauth_ui(self) -> str:
        """Generate OAuth-enabled UI."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Claude Code WebSocket with OAuth</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .auth-section { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
                .authenticated { background-color: #d4fed4; }
                .not-authenticated { background-color: #fed4d4; }
                button { padding: 10px 15px; margin: 5px; cursor: pointer; }
                #messages { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
                .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
                .oauth { background-color: #e6f3ff; }
                .query { background-color: #f0f0f0; }
                .error { background-color: #ffe6e6; }
                .system { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <h1>Claude Code WebSocket with OAuth</h1>
            
            <div id="auth-section" class="auth-section not-authenticated">
                <h3>Authentication Status</h3>
                <p id="auth-status">Not authenticated</p>
                <button onclick="login()">Login with OAuth</button>
                <button onclick="logout()">Logout</button>
                <button onclick="refreshToken()">Refresh Token</button>
                <button onclick="checkStatus()">Check Status</button>
            </div>
            
            <div>
                <h3>Query Claude</h3>
                <input type="text" id="queryInput" placeholder="Enter your query..." style="width: 70%;">
                <button onclick="sendQuery()">Send Query</button>
            </div>
            
            <div id="messages"></div>
            
            <script>
                let ws = null;
                let sessionId = null;
                let authenticated = false;
                
                function connect() {
                    ws = new WebSocket('ws://localhost:8000/ws');
                    
                    ws.onopen = function() {
                        addMessage('Connected to WebSocket', 'system');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleMessage(data);
                    };
                    
                    ws.onclose = function() {
                        addMessage('WebSocket connection closed', 'system');
                    };
                    
                    ws.onerror = function(error) {
                        addMessage('WebSocket error: ' + error, 'error');
                    };
                }
                
                function handleMessage(data) {
                    const type = data.type;
                    
                    if (type === 'connection_established') {
                        sessionId = data.data.session_id;
                        authenticated = data.data.authenticated || false;
                        updateAuthStatus();
                        addMessage('Connection established. Session: ' + sessionId, 'system');
                        
                    } else if (type === 'oauth_login_url') {
                        addMessage('OAuth login URL: ' + data.data.url, 'oauth');
                        
                    } else if (type === 'oauth_success') {
                        authenticated = true;
                        updateAuthStatus();
                        addMessage('OAuth authentication successful!', 'oauth');
                        
                    } else if (type === 'oauth_error') {
                        addMessage('OAuth error: ' + data.data.error, 'error');
                        
                    } else if (type === 'oauth_status') {
                        authenticated = data.data.authenticated;
                        updateAuthStatus();
                        addMessage('Auth status: ' + JSON.stringify(data.data), 'oauth');
                        
                    } else if (type === 'auth_required') {
                        addMessage('Authentication required: ' + data.data.message, 'error');
                        
                    } else if (type === 'query_authenticated') {
                        addMessage('Query authenticated: ' + data.data.message, 'query');
                        
                    } else if (type === 'assistant_message') {
                        for (const block of data.data.content) {
                            if (block.type === 'text') {
                                addMessage('Assistant: ' + block.text, 'query');
                            } else if (block.type === 'tool_use') {
                                addMessage('Tool use: ' + block.name, 'query');
                            }
                        }
                        
                    } else {
                        addMessage(type + ': ' + JSON.stringify(data.data || {}), 'system');
                    }
                }
                
                function updateAuthStatus() {
                    const authSection = document.getElementById('auth-section');
                    const authStatus = document.getElementById('auth-status');
                    
                    if (authenticated) {
                        authSection.className = 'auth-section authenticated';
                        authStatus.textContent = 'Authenticated ✓';
                    } else {
                        authSection.className = 'auth-section not-authenticated';
                        authStatus.textContent = 'Not authenticated ✗';
                    }
                }
                
                function login() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'oauth_login',
                            auto_open: true
                        }));
                    }
                }
                
                function logout() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'oauth_logout'}));
                    }
                }
                
                function refreshToken() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'oauth_refresh'}));
                    }
                }
                
                function checkStatus() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'oauth_status'}));
                    }
                }
                
                function sendQuery() {
                    const input = document.getElementById('queryInput');
                    const query = input.value.trim();
                    
                    if (query && ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'query',
                            prompt: query,
                            options: {}
                        }));
                        input.value = '';
                    }
                }
                
                function addMessage(message, type) {
                    const messages = document.getElementById('messages');
                    const div = document.createElement('div');
                    div.className = 'message ' + type;
                    div.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                    messages.appendChild(div);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                // Connect on page load
                connect();
                
                // Handle Enter key in input
                document.getElementById('queryInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendQuery();
                    }
                });
            </script>
        </body>
        </html>
        """
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.tool_registry_client:
            await self.tool_registry_client.close()
        
        # Cleanup OAuth flows
        for session in self.sessions.values():
            if session.oauth_flow:
                await session.oauth_flow.cleanup()
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the WebSocket server."""
        uvicorn.run(self.app, host=host, port=port)


# Keep the old class name for backward compatibility
ClaudeWebSocketServer = EnhancedClaudeWebSocketServer


if __name__ == "__main__":
    server = EnhancedClaudeWebSocketServer()
    try:
        server.run()
    finally:
        asyncio.run(server.cleanup())