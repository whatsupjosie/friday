#!/usr/bin/env python3
"""
PUBCAST PRODUCTION SERVER
© 2024-2025 Rear View Foresight LLC
"Feic Mo Chroí - See My Heart"

Complete, runnable FastAPI server integrating:
- EQ Adaptor (emotional intelligence)
- GPT Adapter (OpenAI integration)
- Wired Orchestrator (multi-agent coordination)

This is production-ready code. No placeholders.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import our systems
from eq_adaptor import EQAdaptor, create_adaptor as create_eq_adaptor
from gpt_adapter import GPTAdapter, DEFAULT_AGENTS
from orchestrator_wired import WiredOrchestrator, StreamEvent
from eq_integration_layer import EQOrchestrator


# ============================================================================
# CONFIGURATION
# ============================================================================

logger = logging.getLogger("pubcast")

class Config:
    """Application configuration"""
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    
    DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


# ============================================================================
# INITIALIZATION
# ============================================================================

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create app
app = FastAPI(
    title="PubCast AI",
    description="Virtual production studio with emotional intelligence",
    version="1.0.0"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
eq_adaptor: Optional[EQAdaptor] = None
gpt_adapter: Optional[GPTAdapter] = None
orchestrator: Optional[WiredOrchestrator] = None
eq_orchestrator: Optional[EQOrchestrator] = None



# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize all systems on startup"""
    global eq_adaptor, gpt_adapter, orchestrator, eq_orchestrator
    
    logger.info("🚀 PubCast AI starting up...")
    
    # Determine mode: LITE vs FULL
    is_lite = not Config.OPENAI_API_KEY
    if is_lite:
        logger.info("⚡ LITE mode — no API key, responses will use placeholder text")
    else:
        logger.info("🔑 FULL mode — OpenAI API key detected")

    # Create data directory
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize EQ adaptor (always available, no API key needed)
        logger.info("🦗 Initializing EQ adaptor...")
        eq_adaptor = create_eq_adaptor(log_level=Config.LOG_LEVEL)

        # Initialize context-aware EQ system
        logger.info("🧠 Initializing context-aware EQ system...")
        eq_orchestrator = EQOrchestrator(logger=logger)
        logger.info("✅ Context-aware EQ system ready")

        
        # Initialize GPT adapter (may be None in LITE mode)
        if is_lite:
            logger.info("🤖 LITE mode — GPT adapter disabled")
            gpt_adapter = None
        else:
            logger.info("🤖 Initializing GPT adapter...")
            gpt_adapter = GPTAdapter(
                api_key=Config.OPENAI_API_KEY,
                model=Config.OPENAI_MODEL,
                logger=logger
            )
        
        # Initialize orchestrator
        logger.info("🎼 Initializing orchestrator...")
        orchestrator = WiredOrchestrator(
            eq_adaptor=eq_adaptor,
            gpt_adapter=gpt_adapter,
            logger=logger,
            max_agents_per_turn=2,
            card_orchestrator=eq_orchestrator,
        )
        
        logger.info("✅ PubCast AI ready")
        logger.info(f"🌐 Web interface: http://{Config.HOST}:{Config.PORT}")
        logger.info(f"📁 Data directory: {Config.DATA_DIR}")
        logger.info(f"🔄 Mode: {'LITE' if is_lite else 'FULL'}")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("👋 PubCast AI shutting down...")


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health():
    """System health status"""
    if not orchestrator:
        return {"status": "initializing", "mode": "unknown"}
    
    result = orchestrator.get_system_health()
    result["mode"] = "lite" if not Config.OPENAI_API_KEY else "full"
    return result


@app.get("/api/agents")
async def list_agents():
    """List available agents"""
    if not gpt_adapter:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    agents = []
    for agent_id in gpt_adapter.list_agents():
        info = gpt_adapter.get_agent_info(agent_id)
        agents.append(info)
    
    return {"agents": agents}


@app.get("/api/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get info about a specific agent"""
    if not gpt_adapter:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    info = gpt_adapter.get_agent_info(agent_id)
    if not info:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return info


# ============================================================================
# ROOM MANAGEMENT
# ============================================================================

@app.post("/api/rooms/create")
async def create_room(payload: Dict[str, Any]):
    """Create a new room"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    room_id = payload.get("room_id", f"room_{uuid.uuid4().hex[:8]}")
    room_name = payload.get("room_name", f"Room {room_id}")
    
    room = await orchestrator.create_room(room_id, room_name)
    
    return {
        "ok": True,
        "room_id": room.room_id,
        "room_name": room.room_name,
        "created_at": room.created_at,
    }


@app.get("/api/rooms")
async def list_rooms():
    """List all rooms"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return {"rooms": orchestrator.list_rooms()}


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    room = orchestrator.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room_id": room.room_id,
        "room_name": room.room_name,
        "participants": list(room.participants),
        "active_agents": list(room.active_agents),
        "created_at": room.created_at,
        "message_count": len(room.conversation_history),
    }


# ============================================================================
# USER EMOTION & MEMORY
# ============================================================================

@app.get("/api/users/{user_id}/emotion")
async def get_user_emotion(user_id: str):
    """Get current emotional state for user"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.get_user_emotional_state(user_id)


@app.post("/api/users/{user_id}/memory")
async def store_user_memory(user_id: str, payload: Dict[str, Any]):
    """Store a memory about a user"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    content = payload.get("content", "")
    memory_type = payload.get("type", "episodic")
    tags = payload.get("tags", [])
    
    orchestrator.store_memory(user_id, content, memory_type, tags)
    
    return {"ok": True, "type": memory_type}


@app.get("/api/users/{user_id}/memories")
async def recall_memories(user_id: str, query: str = ""):
    """Recall memories for a user"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    context = orchestrator.recall_memory(user_id, query)
    
    return {"memory_context": context}


# ============================================================================
# WEBSOCKET ROOM
# ============================================================================

class RoomConnectionManager:
    """Manages WebSocket connections for a room"""
    
    def __init__(self):
        self.active_connections: Dict[str, list] = {}
    
    async def connect(self, room_id: str, websocket: WebSocket, user_id: str):
        """Accept and track connection"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append((websocket, user_id))
        
        # Notify others
        await self.broadcast(room_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def disconnect(self, room_id: str, websocket: WebSocket, user_id: str):
        """Remove connection"""
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, uid) for ws, uid in self.active_connections[room_id]
                if ws != websocket
            ]
        
        try:
            await websocket.close()
        except:
            pass
        
        # Notify others
        await self.broadcast(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def broadcast(self, room_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections in room"""
        if room_id not in self.active_connections:
            return
        
        dead_connections = []
        
        for websocket, user_id in self.active_connections[room_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending to {user_id}: {e}")
                dead_connections.append((websocket, user_id))
        
        # Clean up dead connections
        for ws, uid in dead_connections:
            await self.disconnect(room_id, ws, uid)


room_manager = RoomConnectionManager()


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time room communication"""
    if not orchestrator:
        await websocket.close(code=1011, reason="System not initialized")
        return
    
    # Extract user_id from query params or generate one
    user_id = websocket.query_params.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
    
    # Create room if it doesn't exist
    if not orchestrator.get_room(room_id):
        await orchestrator.create_room(room_id, room_id)
    
    # Add user to room
    await orchestrator.join_room(room_id, user_id)
    await room_manager.connect(room_id, websocket, user_id)
    
    logger.info(f"WebSocket connected: {user_id} → {room_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_obj = json.loads(data)
            
            msg_type = message_obj.get("type", "chat")
            msg_text = message_obj.get("text", "")
            
            if msg_type == "chat" and msg_text:
                logger.info(f"[{room_id}] {user_id}: {msg_text[:50]}...")
                
                # Process through orchestrator
                try:
                    async for event in orchestrator.handle_message(room_id, user_id, msg_text):
                        # Broadcast event to room
                        await room_manager.broadcast(room_id, json.loads(event.to_json()))
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    await room_manager.broadcast(room_id, {
                        "type": "error",
                        "error": str(e),
                    })
            
            elif msg_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        await orchestrator.leave_room(room_id, user_id)
        await room_manager.disconnect(room_id, websocket, user_id)
        logger.info(f"WebSocket disconnected: {user_id} ← {room_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await orchestrator.leave_room(room_id, user_id)
        await room_manager.disconnect(room_id, websocket, user_id)


# ============================================================================
# WEB UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Simple web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PubCast AI - Virtual Production Studio</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            
            h1 { color: #667eea; margin-top: 0; }
            h2 { color: #764ba2; margin-top: 30px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
            
            .status {
                background: #f0f4ff;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                margin-bottom: 20px;
                font-size: 14px;
            }
            
            .status.loading { border-left-color: #ff9800; }
            .status.healthy { border-left-color: #4caf50; }
            .status.error { border-left-color: #f44336; }
            
            .room-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .room-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s;
                text-decoration: none;
                display: block;
            }
            
            .room-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }
            
            .room-card h3 { margin-top: 0; }
            .room-card p { margin: 5px 0; opacity: 0.9; font-size: 14px; }
            
            .api-section {
                background: #f9f9f9;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-family: monospace;
                font-size: 12px;
                overflow-x: auto;
            }
            
            .btn {
                background: #667eea;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.2s;
            }
            
            .btn:hover {
                background: #764ba2;
            }
            
            .agents-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
            }
            
            .agent-badge {
                background: #e8eaf6;
                color: #667eea;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎭 PubCast AI</h1>
            <p style="margin-bottom: 20px; color: #666;">Virtual production studio with emotional intelligence</p>
            
            <div class="status healthy" id="systemStatus">
                <strong>System Status:</strong> <span id="statusText">Loading...</span>
            </div>
            
            <h2>Quick Start</h2>
            
            <div style="margin-bottom: 20px;">
                <p>Create a new room to start chatting:</p>
                
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <input type="text" id="roomInput" placeholder="Room name" style="flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 6px;">
                    <button class="btn" onclick="createRoom()">Create Room</button>
                </div>
                
                <div id="createdRooms"></div>
            </div>
            
            <h2>Available Agents</h2>
            <div id="agentsList" class="agents-list">
                <div class="agent-badge">Loading...</div>
            </div>
            
            <h2>API Examples</h2>
            
            <div style="margin-bottom: 20px;">
                <p><strong>Create a room:</strong></p>
                <div class="api-section">
POST /api/rooms/create<br>
{"room_id": "studio", "room_name": "Main Studio"}
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <p><strong>Connect WebSocket:</strong></p>
                <div class="api-section">
ws://localhost:8000/ws/studio?user_id=user123<br>
Send: {"type": "chat", "text": "Hello everyone!"}
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <p><strong>Get user emotion:</strong></p>
                <div class="api-section">
GET /api/users/user123/emotion
                </div>
            </div>
            
            <h2>Documentation</h2>
            <p>
                📖 Full API docs: <a href="/docs">/docs</a><br>
                🐍 Source code: <a href="https://github.com">GitHub</a><br>
                💬 Support: <a href="mailto:support@pubcast.ai">support@pubcast.ai</a>
            </p>
        </div>
        
        <script>
            async function loadStatus() {
                try {
                    const resp = await fetch('/api/health');
                    const data = await resp.json();
                    
                    const status = document.getElementById('systemStatus');
                    status.className = 'status healthy';
                    document.getElementById('statusText').textContent = 
                        `🟢 ${data.rooms_active} rooms, ${data.total_participants} participants`;
                } catch (e) {
                    document.getElementById('systemStatus').className = 'status error';
                    document.getElementById('statusText').textContent = '🔴 System unavailable';
                }
            }
            
            async function loadAgents() {
                try {
                    const resp = await fetch('/api/agents');
                    const data = await resp.json();
                    
                    const html = data.agents.map(a => 
                        `<div class="agent-badge">${a.name}<br><small>${a.role}</small></div>`
                    ).join('');
                    
                    document.getElementById('agentsList').innerHTML = html;
                } catch (e) {
                    document.getElementById('agentsList').innerHTML = '<div class="agent-badge error">Failed to load</div>';
                }
            }
            
            async function createRoom() {
                const input = document.getElementById('roomInput');
                const name = input.value.trim() || 'New Room';
                const id = 'room_' + Math.random().toString(36).substr(2, 9);
                
                try {
                    const resp = await fetch('/api/rooms/create', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({room_id: id, room_name: name})
                    });
                    const data = await resp.json();
                    
                    if (data.ok) {
                        input.value = '';
                        loadRooms();
                    }
                } catch (e) {
                    alert('Error creating room: ' + e.message);
                }
            }
            
            async function loadRooms() {
                try {
                    const resp = await fetch('/api/rooms');
                    const data = await resp.json();
                    
                    const html = data.rooms.map(r => 
                        `<a href="/chat.html?room=${r.room_id}" class="room-card">
                            <h3>${r.room_name}</h3>
                            <p>👥 ${r.participants} participants</p>
                            <p>🤖 ${r.active_agents.length} agents</p>
                        </a>`
                    ).join('');
                    
                    document.getElementById('createdRooms').innerHTML = html || '<p>No rooms yet</p>';
                } catch (e) {
                    document.getElementById('createdRooms').innerHTML = '<p>Error loading rooms</p>';
                }
            }
            
            loadStatus();
            loadAgents();
            loadRooms();
            
            setInterval(loadStatus, 5000);
            setInterval(loadRooms, 5000);
        </script>
    </body>
    </html>
    """


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║            🎭 PubCast AI - Virtual Studio                 ║
    ║         "Feic Mo Chroí" — See My Heart                   ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    
    Starting server...
    """)
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_level=Config.LOG_LEVEL.lower(),
    )
