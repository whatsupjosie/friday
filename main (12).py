#!/usr/bin/env python3
"""
PUBCAST PRODUCTION SERVER
© 2024-2025 Rear View Foresight LLC
"Feic Mo Chroí - See My Heart"

Complete, runnable FastAPI server integrating:
- EQ Adaptor (emotional intelligence)
- GPT Adapter (OpenAI integration)
- Wired Orchestrator (multi-agent coordination)
- JWT authentication
- Production-grade WebSocket connection management
"""

import asyncio
import json
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import uvicorn
from fastapi import (
    Depends, FastAPI, HTTPException, Query,
    WebSocket, WebSocketDisconnect, status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    import jwt as pyjwt
except ImportError:
    raise ImportError("PyJWT required. Add 'PyJWT' to requirements.txt and install.")

from eq_adaptor import EQAdaptor, create_adaptor as create_eq_adaptor
from gpt_adapter import GPTAdapter, DEFAULT_AGENTS
from orchestrator_wired import WiredOrchestrator, StreamEvent


# ============================================================================
# CONFIGURATION
# ============================================================================

logger = logging.getLogger("pubcast")


class Config:
    HOST           = os.getenv("HOST", "0.0.0.0")
    PORT           = int(os.getenv("PORT", 8000))
    LOG_LEVEL      = os.getenv("LOG_LEVEL", "INFO")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

    DATA_DIR       = Path(os.getenv("DATA_DIR", "data"))

    # JWT — generate a strong secret at first run; persist it across restarts
    # via the JWT_SECRET env var. Never hard-code.
    JWT_SECRET     = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM  = "HS256"
    JWT_EXPIRY_H   = int(os.getenv("JWT_EXPIRY_HOURS", 24))

    # CORS — restrict to your domain(s) in production.
    # Comma-separated: CORS_ORIGINS=https://pubcast.ai,https://app.pubcast.ai
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# ============================================================================
# JWT HELPERS
# ============================================================================

def create_token(user_id: str) -> str:
    """Issue a signed JWT for user_id."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_H),
    }
    return pyjwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """Decode and validate a JWT. Returns user_id. Raises HTTPException on failure."""
    try:
        payload = pyjwt.decode(
            token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM]
        )
        return payload["sub"]
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ============================================================================
# DEPENDENCY: CURRENT USER (REST endpoints)
# ============================================================================

_bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """FastAPI dependency — validates Bearer token and returns user_id."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def ws_user(token: Optional[str] = Query(default=None)) -> str:
    """FastAPI dependency for WebSocket — validates ?token= query param."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="?token= query param required for WebSocket",
        )
    return decode_token(token)


# ============================================================================
# GLOBAL SYSTEM STATE
# ============================================================================

eq_adaptor:   Optional[EQAdaptor]          = None
gpt_adapter:  Optional[GPTAdapter]         = None
orchestrator: Optional[WiredOrchestrator]  = None


# ============================================================================
# LIFESPAN (replaces deprecated @app.on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup → yield → shutdown."""
    global eq_adaptor, gpt_adapter, orchestrator

    logger.info("🚀 PubCast AI starting up…")

    if not Config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("🦗 Initializing EQ adaptor…")
    eq_adaptor = create_eq_adaptor(log_level=Config.LOG_LEVEL)

    logger.info("🤖 Initializing GPT adapter…")
    gpt_adapter = GPTAdapter(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL,
        logger=logger,
    )

    logger.info("🎼 Initializing orchestrator…")
    orchestrator = WiredOrchestrator(
        eq_adaptor=eq_adaptor,
        gpt_adapter=gpt_adapter,
        logger=logger,
        max_agents_per_turn=2,
    )

    logger.info("✅ PubCast AI ready")
    logger.info(f"🌐 http://{Config.HOST}:{Config.PORT}")

    yield  # ← server runs here

    logger.info("👋 PubCast AI shutting down…")


# ============================================================================
# APP
# ============================================================================

app = FastAPI(
    title="PubCast AI",
    description="Virtual production studio with emotional intelligence",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# AUTH ENDPOINTS  (public — no token required)
# ============================================================================

@app.post("/auth/token")
async def get_token(payload: Dict[str, str]):
    """
    Issue a JWT.  In production, verify credentials against your user store.
    This endpoint accepts any user_id for MVP; gate it with a real credential
    check before launch.
    """
    user_id = payload.get("user_id", "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    token = create_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": Config.JWT_EXPIRY_H,
        "user_id": user_id,
    }


# ============================================================================
# HEALTH & INFO  (public)
# ============================================================================

@app.get("/api/health")
async def health():
    if not orchestrator:
        return {"status": "initializing"}
    return orchestrator.get_system_health()


@app.get("/api/agents")
async def list_agents(_uid: str = Depends(current_user)):
    if not gpt_adapter:
        raise HTTPException(503, "System not initialized")
    return {"agents": [gpt_adapter.get_agent_info(a) for a in gpt_adapter.list_agents()]}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, _uid: str = Depends(current_user)):
    if not gpt_adapter:
        raise HTTPException(503, "System not initialized")
    info = gpt_adapter.get_agent_info(agent_id)
    if not info:
        raise HTTPException(404, "Agent not found")
    return info


# ============================================================================
# ROOM MANAGEMENT
# ============================================================================

@app.post("/api/rooms/create")
async def create_room(payload: Dict[str, Any], _uid: str = Depends(current_user)):
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    import uuid as _uuid
    room_id   = payload.get("room_id",   f"room_{_uuid.uuid4().hex[:8]}")
    room_name = payload.get("room_name", f"Room {room_id}")
    room = await orchestrator.create_room(room_id, room_name)
    return {"ok": True, "room_id": room.room_id, "room_name": room.room_name, "created_at": room.created_at}


@app.get("/api/rooms")
async def list_rooms(_uid: str = Depends(current_user)):
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    return {"rooms": orchestrator.list_rooms()}


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str, _uid: str = Depends(current_user)):
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    room = orchestrator.get_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
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
async def get_emotion(user_id: str, requester: str = Depends(current_user)):
    # Users may only read their own emotional state
    if requester != user_id:
        raise HTTPException(403, "Cannot read another user's emotional state")
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    return orchestrator.get_user_emotional_state(user_id)


@app.post("/api/users/{user_id}/memory")
async def store_memory(user_id: str, payload: Dict[str, Any], requester: str = Depends(current_user)):
    if requester != user_id:
        raise HTTPException(403, "Cannot write to another user's memory")
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    orchestrator.store_memory(
        user_id,
        payload.get("content", ""),
        payload.get("type", "episodic"),
        payload.get("tags", []),
    )
    return {"ok": True}


@app.get("/api/users/{user_id}/memories")
async def recall_memories(user_id: str, query: str = "", requester: str = Depends(current_user)):
    if requester != user_id:
        raise HTTPException(403, "Cannot read another user's memories")
    if not orchestrator:
        raise HTTPException(503, "System not initialized")
    return {"memory_context": orchestrator.recall_memory(user_id, query)}


# ============================================================================
# WEBSOCKET CONNECTION MANAGER  (production-grade)
# ============================================================================

class RoomConnectionManager:
    """
    Manages WebSocket connections with:
    - Safe dead-connection removal during broadcast (no stale sockets)
    - Graceful disconnect notification to remaining participants
    """

    def __init__(self):
        # room_id → list of (websocket, user_id) tuples
        self._connections: Dict[str, List[Tuple[WebSocket, str]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, room_id: str, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(room_id, []).append((websocket, user_id))
        await self._notify(room_id, {"type": "user_joined", "user_id": user_id,
                                     "timestamp": datetime.now().isoformat()},
                           exclude=websocket)

    async def disconnect(self, room_id: str, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            conns = self._connections.get(room_id, [])
            self._connections[room_id] = [(ws, uid) for ws, uid in conns if ws is not websocket]
        try:
            await websocket.close()
        except Exception:
            pass
        await self._notify(room_id, {"type": "user_left", "user_id": user_id,
                                     "timestamp": datetime.now().isoformat()})

    async def broadcast(self, room_id: str, message: Dict[str, Any]) -> None:
        """
        Send to every live connection in the room.
        Dead sockets are removed immediately — no lingering stale connections.
        """
        async with self._lock:
            conns = list(self._connections.get(room_id, []))

        dead: List[Tuple[WebSocket, str]] = []
        for ws, uid in conns:
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.debug(f"Dead connection for {uid}: {exc}")
                dead.append((ws, uid))

        if dead:
            async with self._lock:
                alive = self._connections.get(room_id, [])
                dead_set = {id(ws) for ws, _ in dead}
                self._connections[room_id] = [(ws, uid) for ws, uid in alive if id(ws) not in dead_set]

    async def _notify(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude: Optional[WebSocket] = None,
    ) -> None:
        async with self._lock:
            conns = list(self._connections.get(room_id, []))
        dead: List[Tuple[WebSocket, str]] = []
        for ws, uid in conns:
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append((ws, uid))
        if dead:
            async with self._lock:
                alive = self._connections.get(room_id, [])
                dead_set = {id(ws) for ws, _ in dead}
                self._connections[room_id] = [(ws, uid) for ws, uid in alive if id(ws) not in dead_set]


room_manager = RoomConnectionManager()


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    # JWT passed as ?token= so it's available before the WS handshake completes
    token: Optional[str] = Query(default=None),
):
    # Validate token before accepting the connection
    if not token:
        await websocket.close(code=4001, reason="token required")
        return
    try:
        user_id = decode_token(token)
    except HTTPException as exc:
        await websocket.close(code=4001, reason=exc.detail)
        return

    if not orchestrator:
        await websocket.close(code=1011, reason="System not initialized")
        return

    # Ensure room exists
    if not orchestrator.get_room(room_id):
        await orchestrator.create_room(room_id, room_id)

    await orchestrator.join_room(room_id, user_id)
    await room_manager.connect(room_id, websocket, user_id)
    logger.info(f"WS connected: {user_id} → {room_id}")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "chat")
            msg_text = msg.get("text", "").strip()

            if msg_type == "chat" and msg_text:
                logger.info(f"[{room_id}] {user_id}: {msg_text[:60]}")
                try:
                    async for event in orchestrator.handle_message(room_id, user_id, msg_text):
                        await room_manager.broadcast(room_id, json.loads(event.to_json()))
                except Exception as exc:
                    logger.error(f"Orchestrator error: {exc}", exc_info=True)
                    await room_manager.broadcast(room_id, {"type": "error", "error": str(exc)})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WS error for {user_id}: {exc}", exc_info=True)
    finally:
        await orchestrator.leave_room(room_id, user_id)
        await room_manager.disconnect(room_id, websocket, user_id)
        logger.info(f"WS disconnected: {user_id} ← {room_id}")


# ============================================================================
# WEB UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PubCast AI</title>
  <style>
    :root {
      --ink: #1a1a2e; --mist: #e8eaf6; --violet: #667eea; --plum: #764ba2;
      --care: #4caf50; --warn: #ff9800; --danger: #f44336;
      --radius: 10px; --font: 'Segoe UI', system-ui, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: var(--font); background: linear-gradient(135deg, var(--violet), var(--plum));
           min-height: 100vh; display: flex; align-items: flex-start; justify-content: center; padding: 24px; }
    .shell { width: 100%; max-width: 960px; display: grid; gap: 20px; }
    h1 { color: white; font-size: 1.8rem; margin-bottom: 2px; }
    .tagline { color: rgba(255,255,255,.75); font-style: italic; margin-bottom: 16px; }
    .card { background: white; border-radius: var(--radius); padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
    .pill { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: .75rem; font-weight: 700; }
    .pill-ok { background: #e8f5e9; color: var(--care); }
    .pill-warn { background: #fff8e1; color: var(--warn); }
    .pill-err { background: #ffebee; color: var(--danger); }
    label { display: block; font-size: .85rem; font-weight: 600; margin-bottom: 4px; color: #555; }
    input[type=text], input[type=password] {
      width: 100%; padding: 10px 14px; border: 1.5px solid #ddd; border-radius: 6px;
      font-size: .95rem; transition: border .15s; outline: none; }
    input:focus { border-color: var(--violet); }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer;
           font-size: .9rem; font-weight: 600; transition: opacity .15s; }
    .btn:hover { opacity: .85; }
    .btn-primary { background: var(--violet); color: white; }
    .btn-sm { padding: 6px 14px; font-size: .82rem; }
    .row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
    #messages { height: 320px; overflow-y: auto; border: 1.5px solid #eee;
                border-radius: 8px; padding: 14px; background: #fafafa; }
    .msg { padding: 8px 12px; margin-bottom: 8px; border-radius: 8px; font-size: .9rem; line-height: 1.45; }
    .msg-user { background: var(--mist); text-align: right; }
    .msg-agent { background: #f3e5f5; border-left: 3px solid var(--plum); }
    .msg-system { background: #e8f5e9; color: #388e3c; font-size: .8rem; font-style: italic; }
    .msg-err { background: #ffebee; color: var(--danger); font-size: .82rem; }
    .agent-name { font-weight: 700; color: var(--plum); margin-bottom: 3px; font-size: .8rem; }
    .care-badge { font-size: .72rem; color: #888; margin-left: 8px; }
    .agents-grid { display: flex; gap: 10px; flex-wrap: wrap; }
    .agent-tile { background: var(--mist); border-radius: 8px; padding: 12px 16px; min-width: 140px; }
    .agent-tile strong { display: block; color: var(--plum); margin-bottom: 4px; }
    .agent-tile small { color: #666; font-size: .78rem; }
    #authSection { background: white; border-radius: var(--radius); padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
    #chatSection { display: none; }
  </style>
</head>
<body>
<div class="shell">
  <div>
    <h1>🎭 PubCast AI</h1>
    <p class="tagline">Feic Mo Chroí — See My Heart</p>
  </div>

  <!-- AUTH -->
  <div class="card" id="authSection">
    <h2 style="margin-bottom:16px">Sign In</h2>
    <div style="max-width:360px; display:grid; gap:12px;">
      <div>
        <label>Your name / user ID</label>
        <input type="text" id="authUserId" placeholder="josie" autocomplete="username">
      </div>
      <button class="btn btn-primary" onclick="signIn()">Get Access Token</button>
      <p id="authError" style="color:var(--danger);font-size:.85rem;display:none"></p>
    </div>
  </div>

  <!-- MAIN CHAT UI (shown after auth) -->
  <div id="chatSection">
    <div class="card" style="margin-bottom:16px">
      <div class="row" style="justify-content:space-between; align-items:center;">
        <div>
          <span id="statusPill" class="pill pill-warn">Connecting…</span>
          <span class="care-badge">Care level: <strong id="careLevelLabel">—</strong></span>
        </div>
        <span style="font-size:.82rem;color:#888">Room: <strong id="roomLabel">studio</strong></span>
      </div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <div id="messages"></div>
      <div class="row" style="margin-top:12px">
        <input type="text" id="msgInput" placeholder="Say something…" style="flex:1"
               onkeydown="if(event.key==='Enter')sendMsg()">
        <button class="btn btn-primary" onclick="sendMsg()">Send</button>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-bottom:12px;color:var(--plum)">Available Agents</h3>
      <div class="agents-grid" id="agentsGrid"><em style="color:#aaa">Loading…</em></div>
    </div>
  </div>
</div>

<script>
// ── state ──────────────────────────────────────────────────────────────────
let TOKEN = null, USER_ID = null, ws = null;
const ROOM_ID = 'studio';
// Per-agent streaming buffers: agent_id → DOM element currently streaming
const agentBuffers = {};

// ── auth ───────────────────────────────────────────────────────────────────
async function signIn() {
  const uid = document.getElementById('authUserId').value.trim();
  if (!uid) return;
  try {
    const r = await fetch('/auth/token', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: uid})
    });
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    TOKEN = d.access_token;
    USER_ID = d.user_id;
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    document.getElementById('roomLabel').textContent = ROOM_ID;
    initRoom();
  } catch (e) {
    const el = document.getElementById('authError');
    el.textContent = e.message;
    el.style.display = 'block';
  }
}

// ── room setup ─────────────────────────────────────────────────────────────
async function initRoom() {
  // Create studio room if it doesn't exist
  await fetch('/api/rooms/create', {
    method: 'POST',
    headers: {'Content-Type':'application/json', Authorization:`Bearer ${TOKEN}`},
    body: JSON.stringify({room_id: ROOM_ID, room_name: 'Main Studio'})
  });
  loadAgents();
  connectWS();
}

async function loadAgents() {
  try {
    const r = await fetch('/api/agents', {headers:{Authorization:`Bearer ${TOKEN}`}});
    const d = await r.json();
    document.getElementById('agentsGrid').innerHTML = d.agents.map(a =>
      `<div class="agent-tile"><strong>${a.name}</strong><small>${a.role}</small></div>`
    ).join('');
  } catch {}
}

// ── websocket ──────────────────────────────────────────────────────────────
function connectWS() {
  const url = `ws://${location.host}/ws/${ROOM_ID}?token=${TOKEN}`;
  ws = new WebSocket(url);

  ws.onopen = () => setPill('🟢 Connected', 'ok');
  ws.onclose = () => { setPill('🔴 Disconnected', 'err'); setTimeout(connectWS, 3000); };
  ws.onerror = () => setPill('⚠️ WS Error', 'err');

  ws.onmessage = ({data}) => {
    const msg = JSON.parse(data);

    if (msg.type === 'agent_start') {
      // Begin a new agent bubble — all subsequent chunks for this agent_id go here
      const el = addBubble('agent', '', msg.agent_id, msg.payload?.care_level);
      agentBuffers[msg.agent_id] = el;

    } else if (msg.type === 'stream_chunk') {
      // Append to the correct agent's bubble
      const el = agentBuffers[msg.agent_id];
      if (el) {
        const body = el.querySelector('.agent-body');
        if (body) body.textContent += msg.payload?.chunk ?? '';
      }

    } else if (msg.type === 'agent_done') {
      // Finalise — remove buffer reference
      delete agentBuffers[msg.agent_id];

    } else if (msg.type === 'error') {
      addRaw('err', `⚠ ${msg.error}`);

    } else if (msg.type === 'user_joined') {
      if (msg.user_id !== USER_ID)
        addRaw('system', `${msg.user_id} joined`);

    } else if (msg.type === 'user_left') {
      addRaw('system', `${msg.user_id} left`);
    }
  };
}

// ── message send ───────────────────────────────────────────────────────────
function sendMsg() {
  const inp = document.getElementById('msgInput');
  const text = inp.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
  addBubble('user', text);
  ws.send(JSON.stringify({type:'chat', text}));
  inp.value = '';
}

// ── DOM helpers ────────────────────────────────────────────────────────────
function addBubble(role, text, agentId, careLabel) {
  const box = document.getElementById('messages');
  const div = document.createElement('div');
  if (role === 'user') {
    div.className = 'msg msg-user';
    div.textContent = text;
  } else {
    div.className = 'msg msg-agent';
    div.innerHTML =
      `<div class="agent-name">${agentId ?? ''}${careLabel ? `<span class="care-badge">${careLabel}</span>` : ''}</div>`+
      `<div class="agent-body"></div>`;
  }
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function addRaw(type, text) {
  const box = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `msg msg-${type}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function setPill(text, state) {
  const el = document.getElementById('statusPill');
  el.textContent = text;
  el.className = `pill pill-${state}`;
}
</script>
</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║          🎭 PubCast AI — Virtual Studio               ║
    ║       "Feic Mo Chroí" — See My Heart                 ║
    ╚════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_level=Config.LOG_LEVEL.lower(),
    )
