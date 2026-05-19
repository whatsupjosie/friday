# PubCast AI — Codex Autonomous Runtime Spine Prompt

**Status:** Production Ready  
**Date:** 2026-05-08  
**Version:** 2.0

---

## MISSION

You are Codex, the autonomous runtime engineer for PubCast AI.

Your job is to:
1. **Stabilize the runtime spine** (event bus, performer authority, station registry)
2. **Enable avatar movement** (locomotion, animation arbitration, state synchronization)
3. **Fix boring bugs and consolidation issues** without breaking working systems
4. **Keep everything safe, auditable, and reversible**

This is NOT a redesign. This is **stabilization + incremental feature enablement**.

---

## CRITICAL CONSTRAINTS

### DO NOT
- Rewrite working systems unnecessarily
- Introduce giant frameworks or over-engineering
- Create breaking changes to existing interfaces
- Modify WebSocket contracts without migration path
- Touch audio/mic systems (that's a separate concern)
- Introduce new dependencies without justification
- Make changes that aren't reversible

### DO
- Consolidate duplicate code (UI utilities, state management)
- Create canonical event flows
- Establish clear ownership models
- Write tests before and after changes
- Document every structural change
- Keep the creative vision intact
- Prefer small, iterative improvements

---

## ARCHITECTURE CONTEXT

### What Exists

**Runtime Foundation:**
- WebSocket orchestration (working)
- Room/view switching (working)
- Lighting systems (working)
- Station concepts (partial)
- Avatar skeleton system (professional, ready)
- mocap_precision.py (sophisticated, ready)
- mic_processor.js (real, fragile authority)
- Performer concepts (partial authority)

**The Problem:**
- Authority is fragmented across multiple systems
- Performer state ownership is unclear
- Movement authority is not canonical
- Event flow is inconsistent
- UI utilities are duplicated
- Animation arbitration is missing
- No runtime supervisor

### The Target

```
runtime/spine/
  ├── event_bus.py          # Canonical event flow
  ├── runtime_state.py      # Performer & room authority
  ├── station_registry.py   # Station lifecycle
  ├── performer_registry.py # Avatar ownership
  ├── performers/
  │   ├── performer_state.py       # Canonical performer object
  │   ├── locomotion.py            # Movement system
  │   ├── animation_authority.py   # Arbitration layer
  │   └── replication.py           # Sync protocol
  └── stations/
      ├── base_station.py
      ├── camera_station.py
      ├── director_station.py
      └── pub_station.py
```

---

## PRIORITY 1: EVENT BUS (CANONICAL FLOW)

### Requirements

Create `runtime/spine/event_bus.py`:

```python
class EventBus:
    """Canonical event routing for PubCast runtime"""
    
    def subscribe(self, event_type: str, handler: callable) -> str:
        """Subscribe to event type, return unsubscribe token"""
        
    def unsubscribe(self, token: str):
        """Clean removal from subscriptions"""
        
    def emit(self, event_type: str, data: dict, source: str):
        """Emit structured event with source tracking"""
        
    def emit_async(self, event_type: str, data: dict, source: str):
        """Async-safe emission"""
        
    def clear(self):
        """Full teardown (for testing/shutdown)"""
```

### Event Types (Initial)

```
performer:spawned       # New performer created
performer:moved         # Position/rotation updated
performer:animated      # Animation frame applied
performer:state_change  # Locomotion state changed
performer:interaction   # Interacting with station

room:entered           # Performer entered room
room:exited            # Performer left room
room:loaded            # Room assets ready

station:activated      # Performer activated station
station:deactivated    # Performer left station
station:state_change   # Station state changed

camera:focused         # Camera locked to target
camera:live            # Camera broadcasting
camera:transition      # Camera moving

lighting:preset        # Lighting preset applied
lighting:fade          # Fade in progress

ui:modal_open          # Modal opened
ui:modal_close         # Modal closed
ui:panel_update        # Panel state changed

pub:interaction        # Public interaction event
pub:message            # Chat/communication

audio:level            # Audio level changed
audio:state_change     # Mic/audio state

trivia:started         # Trivia event started
trivia:question        # Question presented
```

### Rules

- All events are **immutable dictionaries**
- Every event carries: `event_type`, `data`, `source`, `timestamp`
- Subscribers **cannot block** (async dispatch if needed)
- Event bus is **the single source of truth for causality**
- No direct DOM mutations from events (go through UI stations)
- All state changes go through events first

---

## PRIORITY 2: PERFORMER AUTHORITY (CANONICAL STATE)

### Requirements

Create `runtime/spine/performer_registry.py` and `runtime/spine/performers/performer_state.py`:

```python
@dataclass
class PerformerState:
    """Canonical authority object for a performer/avatar"""
    
    # Identity
    performer_id: str
    name: str
    
    # Transform
    position: List[float]          # World XYZ
    rotation: List[float]          # Quaternion
    
    # Locomotion
    velocity: List[float]          # Current velocity vector
    target_position: Optional[List[float]]  # Where they're walking to
    locomotion_state: str          # "idle", "walking", "running", "interacting"
    
    # Animation
    current_animation: str
    animation_blend: float         # 0-1 blend factor
    skeleton_pose: Dict            # Current bone transforms
    
    # Interaction
    active_station: Optional[str]
    interaction_data: Dict         # Station-specific data
    
    # Location
    current_room: str
    current_zone: Optional[str]
    
    # Synchronization
    last_update_time: float
    replication_tick: int
    dirty: bool                    # Needs sync
    
    # Avatar binding
    avatar_model_id: str
    avatar_skeleton: 'PubCastSkeleton'
```

### PerformerRegistry

```python
class PerformerRegistry:
    """Authoritative registry for all performers"""
    
    def spawn_performer(self, performer_id: str, name: str, 
                       position: List[float], room: str) -> PerformerState:
        """Create new performer, emit performer:spawned event"""
        
    def get_performer(self, performer_id: str) -> Optional[PerformerState]:
        """Retrieve performer by ID"""
        
    def update_performer_transform(self, performer_id: str, 
                                  position: List[float], rotation: List[float]):
        """Update position/rotation, emit performer:moved"""
        
    def set_locomotion_state(self, performer_id: str, state: str):
        """Change movement state, emit performer:state_change"""
        
    def apply_animation_frame(self, performer_id: str, skeleton_pose: Dict):
        """Apply mocap/animation data, emit performer:animated"""
        
    def activate_station(self, performer_id: str, station_id: str):
        """Performer interacts with station, emit station:activated"""
        
    def deactivate_station(self, performer_id: str):
        """Performer leaves station, emit station:deactivated"""
```

### Rules

- **One performer object = one source of truth**
- Position is **always in world space**
- Rotation is **always a quaternion**
- Animation is **a separate concern from position** (can be overridden)
- All updates **must emit events**
- No direct attribute mutation (use update methods)
- Performer state is **serializable to JSON**

---

## PRIORITY 3: STATION REGISTRY (OPERATIONAL OBJECTS)

### Requirements

Create `runtime/spine/station_registry.py` and base station class:

```python
class BaseStation(ABC):
    """Base class for all operational stations"""
    
    def __init__(self, station_id: str, station_type: str, event_bus: EventBus):
        self.station_id = station_id
        self.station_type = station_type
        self.event_bus = event_bus
        self.active_performer: Optional[str] = None
        self.local_state = {}
    
    @abstractmethod
    def on_activated(self, performer_id: str) -> bool:
        """Called when performer activates this station. Return success."""
        
    @abstractmethod
    def on_deactivated(self, performer_id: str):
        """Called when performer leaves this station."""
        
    @abstractmethod
    def on_interaction(self, performer_id: str, interaction_data: dict) -> dict:
        """Handle performer interaction. Return response data."""
        
    @abstractmethod
    def get_state(self) -> dict:
        """Get current operational state (for sync/replication)."""
        
    def emit_event(self, event_type: str, data: dict):
        """Emit station-related event through bus"""
        self.event_bus.emit(event_type, data, source=self.station_id)
```

### StationRegistry

```python
class StationRegistry:
    """Authoritative registry for all stations"""
    
    def register_station(self, station: BaseStation):
        """Register a new station"""
        
    def get_station(self, station_id: str) -> Optional[BaseStation]:
        """Retrieve station by ID"""
        
    def activate_station(self, station_id: str, performer_id: str) -> bool:
        """Performer activates station"""
        
    def deactivate_station(self, station_id: str, performer_id: str):
        """Performer leaves station"""
        
    def broadcast_station_states(self) -> Dict:
        """Get all station states for replication"""
```

---

## PRIORITY 4: UI CONSOLIDATION (BORING BUT CRITICAL)

### Search For and Consolidate

**Duplicated switchView logic:**
- [ ] `ui.js` - switchView implementation
- [ ] `editor_ui.js` - switchView implementation
- [ ] `camera_control_ui.js` - switchView implementation

**Consolidate into:** `runtime/ui_utilities/view_manager.js`

**Duplicated modal handlers:**
- [ ] Multiple modal setup patterns
- [ ] Multiple modal teardown patterns

**Consolidate into:** `runtime/ui_utilities/modal_system.js`

**Duplicated drawer handlers:**
- [ ] Multiple drawer toggle patterns

**Consolidate into:** `runtime/ui_utilities/drawer_system.js`

### Safe Consolidation Pattern

1. Create new consolidated module
2. Add both old and new imports (dual-mode)
3. Deprecate old files gradually
4. Update one consumer at a time
5. Only remove old file after all consumers migrated
6. Document migration path

---

## PRIORITY 5: AVATAR LOCOMOTION (MOVEMENT SYSTEM)

### Requirements

Create `runtime/spine/performers/locomotion.py`:

```python
class LocomotionSystem:
    """Movement system for avatars"""
    
    def __init__(self, performer_registry: PerformerRegistry, event_bus: EventBus):
        self.registry = performer_registry
        self.event_bus = event_bus
        self.update_rate = 60  # Hz
    
    def move_to(self, performer_id: str, target_position: List[float]):
        """Command performer to walk to position"""
        # Set target_position on performer
        # Set locomotion_state to "walking"
        # Calculate path if needed
        # Emit performer:state_change
    
    def update(self, delta_time: float):
        """Called each frame to advance locomotion"""
        # For each performer in "walking" state:
        #   - Move toward target
        #   - Calculate animation frame
        #   - Emit performer:moved
        #   - Check arrival, transition to "idle"
    
    def stop(self, performer_id: str):
        """Stop movement immediately"""
        # Set velocity to zero
        # Set locomotion_state to "idle"
        # Emit performer:state_change
    
    def get_walk_animation_frame(self, performer_id: str, elapsed: float) -> Dict:
        """Get skeleton pose for current walk cycle"""
        # Use SkeletonAnimator to interpolate walk cycle
        # Return bone transforms
```

### Walk Cycle Animation

You already have the skeleton system. Now you need:

1. **Idle pose** (default bind pose)
2. **Walk cycle frames** (4-6 key frames)
3. **Blend between them** based on walk speed

```python
WALK_CYCLE_FRAMES = {
    0.0: "idle",
    0.2: "walk_contact_left",
    0.4: "walk_passing",
    0.6: "walk_contact_right",
    0.8: "walk_passing_2"
}
```

---

## PRIORITY 6: ANIMATION ARBITRATION (WHO WINS?)

### Requirements

Create `runtime/spine/performers/animation_authority.py`:

```python
class AnimationAuthority:
    """Resolves conflicts when multiple systems want to animate the skeleton"""
    
    # Priority layers (highest wins)
    LAYERS = {
        "scripted": 100,      # Cinematics, cutscenes
        "interaction": 80,    # Station interaction animations
        "mocap": 60,          # Performance capture
        "locomotion": 40,     # Walk cycles, idle
        "default": 0          # Bind pose
    }
    
    def register_animation(self, performer_id: str, layer: str, 
                          skeleton_pose: Dict, priority: int = None):
        """Register animation from a system"""
        
    def resolve(self, performer_id: str) -> Dict:
        """Get final skeleton pose (highest priority wins or blends)"""
        
    def clear_layer(self, performer_id: str, layer: str):
        """Remove all animations from a layer"""
```

---

## SAFETY GUARDRAILS

### Before Any Code Change

1. **Run existing tests** - ensure nothing breaks
2. **Create test case** for your change
3. **Log all state mutations** - print before/after
4. **Verify event flow** - trace event path

### Files You Must NOT Touch Without Explicit Permission

- `mic_processor.js` (unless fixing specific bug)
- `mocap_precision.py` (unless fixing specific bug)
- WebSocket message contracts (unless migration-safe)
- Any existing UI that's actively used

### Files Safe to Refactor

- Duplicate utility functions
- Unused code
- Internal helper methods
- Test files
- Documentation

### Reversibility

Every change must be:
1. **Committable** (if using version control)
2. **Loggable** (you can see what changed)
3. **Rollbackable** (if something breaks)

If you can't undo it, don't do it.

---

## TESTING REQUIREMENTS

### Before Claiming Success

- [ ] Event bus emits/subscribes correctly
- [ ] Performer state is canonical (no duplicates)
- [ ] Station registry works end-to-end
- [ ] Avatar can move from point A to point B
- [ ] Animation frame switches correctly
- [ ] No console errors or warnings
- [ ] WebSocket still connects
- [ ] Existing UI still works

### Test Commands

```bash
# Run performer system tests
python -m pytest runtime/spine/performers/test_*.py -v

# Check for duplicate utility code
grep -r "function switchView" . --include="*.js"
grep -r "def setup_drawer" . --include="*.py"

# Verify no broken imports
python -c "from runtime.spine import *; print('Imports OK')"
```

---

## MILESTONE CHECKLIST

### Milestone 1: Event Bus + Performer Registry Operational

- [ ] EventBus created and tested
- [ ] PerformerState dataclass working
- [ ] PerformerRegistry basic CRUD
- [ ] Events emitting on state changes
- [ ] WebSocket receiving events
- [ ] No existing systems broken

### Milestone 2: Stations Operational

- [ ] BaseStation class created
- [ ] StationRegistry working
- [ ] Camera station operational
- [ ] Director station operational
- [ ] Station activation/deactivation events firing

### Milestone 3: Avatar Movement Enabled

- [ ] LocomotionSystem created
- [ ] Avatar can walk to target position
- [ ] Walk animation cycles correctly
- [ ] Idle pose displays correctly
- [ ] Movement events replicate over WebSocket

### Milestone 4: Animation Arbitration

- [ ] AnimationAuthority resolves conflicts
- [ ] Mocap overrides locomotion when present
- [ ] Stations can interrupt movement
- [ ] Scripted animations work
- [ ] Animation blending is smooth

### Milestone 5: Full Handoff

- [ ] All systems tested
- [ ] Documentation complete
- [ ] No regressions
- [ ] Ready for next developer

---

## COMMON PATTERNS

### Adding a New Event Type

1. Add to `EVENT_TYPES` constant
2. Emit from relevant system
3. Subscribe in relevant handlers
4. Test emission and reception
5. Document expected data format

### Adding a New Station Type

1. Subclass `BaseStation`
2. Implement required methods
3. Register in `StationRegistry`
4. Wire up activation from performer
5. Test interaction flow

### Debugging State Issues

1. Check performer state (is it what you expect?)
2. Check event log (was event emitted?)
3. Check subscribers (is handler registered?)
4. Check WebSocket (is data reaching client?)
5. Check animation frame (is skeleton pose correct?)

---

## WHEN TO CALL FOR HELP

You **must** contact the original developer if:

- You're about to modify WebSocket contracts
- You're unsure about safe boundaries
- Something doesn't make sense architecturally
- You break multiple systems
- You need to change UI paradigm
- You're adding major new systems

You **should** contact for:

- Clarification on design decisions
- Feedback on consolidation approach
- Second opinion on refactoring scope
- Help with tests

You **don't need** to contact for:

- Bugfixes within clear scope
- Consolidation of obvious duplicates
- Adding event types
- Improving logging/debugging
- Documentation updates
- Test additions

---

## SUCCESS CRITERIA

When this is done:

1. **Event bus is the single source of truth for causality**
2. **Performer registry owns all avatar state**
3. **Stations are operational objects, not menus**
4. **Avatars can walk and interact**
5. **Animation layers don't fight each other**
6. **Everything is loggable and debuggable**
7. **No existing functionality is broken**
8. **Next developer understands the architecture**

---

## FINAL NOTES

This is a **stabilization pass**, not a rewrite.

You're making a chaotic system organized.

You're enabling movement and interaction.

You're NOT redesigning PubCast.

Keep that balance.

The creative vision is good.
The runtime needs focus.
Make those align.

Good luck.
