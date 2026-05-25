# Unified PubCast Runtime Package

## Repository Layout

```text
pubcast_runtime/
│
├── runtime/
│   ├── __init__.py
│   ├── spine.py
│   ├── hub.py
│   ├── events.py
│   ├── contracts.py
│   ├── registry.py
│   ├── pub_manager.py
│   ├── eq/
│   │   ├── __init__.py
│   │   ├── input_scorer.py
│   │   ├── jeremy.py
│   │   ├── vdi.py
│   │   └── decision_engine.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pete.py
│   │   ├── epete.py
│   │   ├── jeeves.py
│   │   ├── evo.py
│   │   └── memory_service.py
│   ├── persistence/
│   │   ├── snapshots.py
│   │   ├── journals.py
│   │   └── sanctuary.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── websocket_bridge.py
│
├── tests/
│   ├── test_pub_manager.py
│   ├── test_spine.py
│   ├── test_event_bus.py
│   └── test_eq_pipeline.py
│
├── main.py
├── requirements.txt
└── README.md
```

---

# runtime/events.py

```python
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import uuid


@dataclass
class SpineEvent:
    source: str
    domain: str
    event_type: str

    authority: str = "runtime"

    emotional_state: Dict = field(default_factory=dict)
    runtime_state: Dict = field(default_factory=dict)
    establishment_state: Dict = field(default_factory=dict)

    policy_changes: List = field(default_factory=list)
    requested_actions: List = field(default_factory=list)

    continuity_priority: str = "normal"
    risk_level: str = "normal"

    metadata: Dict = field(default_factory=dict)

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

---

# runtime/contracts.py

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class RuntimeService:
    name: str
    authority_level: str

    capabilities: List[str] = field(default_factory=list)
    subscribes_to: List[str] = field(default_factory=list)
    publishes: List[str] = field(default_factory=list)

    def registration_payload(self):
        return {
            "name": self.name,
            "authority": self.authority_level,
            "capabilities": self.capabilities,
            "subscribes_to": self.subscribes_to,
            "publishes": self.publishes,
        }
```

---

# runtime/hub.py

```python
from collections import defaultdict


class EventHub:
    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event_name, callback):
        self.listeners[event_name].append(callback)

    def publish(self, event_name, payload):
        for callback in self.listeners[event_name]:
            callback(payload)


hub = EventHub()
```

---

# runtime/spine.py

```python
from runtime.hub import hub


class Spine:
    """
    Authoritative runtime coordinator.
    """

    def __init__(self):
        self.services = {}
        self.state = {
            "mode": "open",
            "risk": "normal",
        }

    def register_service(self, payload):
        self.services[payload["name"]] = payload

    def publish_event(self, event_name, payload):
        hub.publish(event_name, payload)

    def update_state(self, key, value):
        self.state[key] = value

    def status(self):
        return {
            "services": list(self.services.keys()),
            "state": self.state,
        }


spine = Spine()
```

---

# runtime/pub_manager.py

```python
from dataclasses import dataclass
from enum import Enum


class EstablishmentMode(str, Enum):
    OPEN = "open"
    LATE_NIGHT = "late_night"
    QUIET = "quiet"
    CROWDED = "crowded"
    RECOVERY = "recovery"
    EMERGENCY = "emergency"


class RiskLevel(str, Enum):
    NORMAL = "normal"
    STRAINED = "strained"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class PubVitals:
    cpu_percent: int = 10
    memory_percent: int = 20
    active_recordings: int = 0
    pending_heavy_jobs: int = 0
    active_rooms: int = 0
    active_guests: int = 0
    failed_services: int = 0
    idle_toolkits: int = 0


@dataclass
class EstablishmentPolicy:
    admit_new_guests: bool = True
    allow_heavy_generation: bool = True
    allow_background_simulation: bool = True
    allow_new_rooms: bool = True

    ask_jeeves_to_shelve_idle: bool = False
    ask_epete_to_reduce_background_work: bool = False
    ask_pete_to_limit_floor_activity: bool = False

    prefer_deferred_jobs: bool = False
    prefer_hibernation: bool = False

    ai_activity_level: str = "normal"


@dataclass
class PubDecision:
    mode: EstablishmentMode
    risk: RiskLevel
    policy: EstablishmentPolicy

    def to_dict(self):
        return {
            "mode": self.mode.value,
            "risk": self.risk.value,
            "policy": self.policy.__dict__,
        }


class PubManager:
    doctrine = "declarative_not_operational"

    def __init__(self):
        self._mode = EstablishmentMode.OPEN
        self._risk = RiskLevel.NORMAL

    def evaluate(self, vitals: PubVitals):
        mode = EstablishmentMode.OPEN
        risk = RiskLevel.NORMAL
        policy = EstablishmentPolicy()

        if vitals.cpu_percent >= 95:
            mode = EstablishmentMode.EMERGENCY
            risk = RiskLevel.EMERGENCY

            policy.allow_new_rooms = False
            policy.prefer_hibernation = True
            policy.allow_heavy_generation = False

        elif vitals.failed_services > 0:
            mode = EstablishmentMode.RECOVERY
            risk = RiskLevel.HIGH

            policy.admit_new_guests = False
            policy.allow_background_simulation = False
            policy.ai_activity_level = "minimal"

        elif vitals.memory_percent >= 80:
            mode = EstablishmentMode.CROWDED
            risk = RiskLevel.STRAINED

            policy.admit_new_guests = False
            policy.prefer_deferred_jobs = True

        elif vitals.cpu_percent >= 70 and vitals.active_recordings > 0:
            mode = EstablishmentMode.QUIET

            policy.admit_new_guests = False
            policy.allow_heavy_generation = False
            policy.ask_jeeves_to_shelve_idle = True
            policy.ask_epete_to_reduce_background_work = True
            policy.ask_pete_to_limit_floor_activity = True

        elif vitals.idle_toolkits >= 5:
            mode = EstablishmentMode.LATE_NIGHT
            policy.ask_jeeves_to_shelve_idle = True

        self._mode = mode
        self._risk = risk

        return PubDecision(
            mode=mode,
            risk=risk,
            policy=policy,
        )

    def status(self):
        return {
            "doctrine": self.doctrine,
            "boundaries": [
                "does_not_open_sockets",
                "does_not_clean_folders",
                "does_not_execute_workers",
            ],
            "policy": {
                "mode": self._mode.value,
                "risk": self._risk.value,
            },
        }

    def registration_payload(self):
        return {
            "name": "pub_manager",
            "authority": "declarative_policy_only",
            "capabilities": [
                "establishment_policy",
                "runtime_posture",
                "load_governance",
            ],
        }


pub_manager = PubManager()
```

---

# runtime/eq/input_scorer.py

```python
class InputScorer:
    def score(self, text: str):
        urgency = "normal"

        if "help" in text.lower():
            urgency = "high"

        return {
            "urgency": urgency,
            "length": len(text),
        }
```

---

# runtime/eq/jeremy.py

```python
class JeremyCricket:
    """
    Emotional posture advisor.
    Never operational authority.
    """

    def evaluate(self, text: str):
        emotional_tone = "neutral"

        if "worried" in text:
            emotional_tone = "concerned"

        return {
            "tone": emotional_tone,
            "continuity_priority": "high",
        }
```

---

# runtime/eq/vdi.py

```python
class VDIEngine:
    def interpret(self, emotional_signal, score):
        return {
            "response_style": "supportive",
            "urgency": score["urgency"],
            "tone": emotional_signal["tone"],
        }
```

---

# runtime/eq/decision_engine.py

```python
class DecisionEngine:
    def decide(self, vdi_output):
        return {
            "allow_generation": True,
            "priority": vdi_output["urgency"],
        }
```

---

# runtime/services/pete.py

```python
class Pete:
    def registration_payload(self):
        return {
            "name": "pete",
            "authority": "social_runtime",
            "capabilities": [
                "guest_interaction",
                "social_continuity",
            ],
        }
```

---

# runtime/services/epete.py

```python
class EPete:
    def registration_payload(self):
        return {
            "name": "epete",
            "authority": "technical_runtime",
            "capabilities": [
                "background_jobs",
                "task_execution",
            ],
        }
```

---

# runtime/services/jeeves.py

```python
class Jeeves:
    def registration_payload(self):
        return {
            "name": "jeeves",
            "authority": "restoration_and_order",
            "capabilities": [
                "recovery",
                "toolkit_shelving",
                "continuity_preservation",
            ],
        }
```

---

# runtime/services/evo.py

```python
class EVO:
    def registration_payload(self):
        return {
            "name": "evo",
            "authority": "runtime_fidelity",
            "capabilities": [
                "optimization",
                "performance_tuning",
            ],
        }
```

---

# runtime/services/memory_service.py

```python
class MemoryService:
    def registration_payload(self):
        return {
            "name": "memory_service",
            "authority": "persistence",
            "capabilities": [
                "journaling",
                "snapshots",
                "continuity_memory",
            ],
        }
```

---

# runtime/api/routes.py

```python
from fastapi import APIRouter

from runtime.pub_manager import pub_manager, PubVitals
from runtime.spine import spine


router = APIRouter()


@router.get("/api/spine/status")
def spine_status():
    return spine.status()


@router.get("/api/spine/pub-manager/status")
def pub_manager_status():
    vitals = PubVitals()
    decision = pub_manager.evaluate(vitals)
    return decision.to_dict()


@router.get("/api/spine/pub-manager/policy")
def pub_manager_policy():
    return pub_manager.status()
```

---

# main.py

```python
from fastapi import FastAPI
import uvicorn

from runtime.api.routes import router
from runtime.spine import spine

from runtime.pub_manager import pub_manager

from runtime.services.pete import Pete
from runtime.services.epete import EPete
from runtime.services.jeeves import Jeeves
from runtime.services.evo import EVO
from runtime.services.memory_service import MemoryService


app = FastAPI(title="Unified PubCast Runtime")

app.include_router(router)


services = [
    pub_manager,
    Pete(),
    EPete(),
    Jeeves(),
    EVO(),
    MemoryService(),
]


for service in services:
    spine.register_service(service.registration_payload())


@app.get("/")
def root():
    return {
        "runtime": "Unified PubCast Runtime",
        "status": "online",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

# tests/test_pub_manager.py

```python
from runtime.pub_manager import EstablishmentMode, PubManager, PubVitals, RiskLevel


def test_pub_manager_open_by_default():
    manager = PubManager()
    decision = manager.evaluate(PubVitals())
    assert decision.mode == EstablishmentMode.OPEN
    assert decision.risk == RiskLevel.NORMAL
    assert decision.policy.admit_new_guests is True
    assert decision.policy.allow_heavy_generation is True


def test_pub_manager_quiet_protects_active_recording():
    manager = PubManager()
    decision = manager.evaluate(
        PubVitals(
            cpu_percent=74,
            active_recordings=1,
            pending_heavy_jobs=2,
            idle_toolkits=3,
        )
    )

    assert decision.mode == EstablishmentMode.QUIET
    assert decision.policy.admit_new_guests is False
    assert decision.policy.allow_heavy_generation is False
```

---

# requirements.txt

```text
fastapi
uvicorn
pytest
pydantic
```

---

# README.md

```markdown
# Unified PubCast Runtime

A declarative emotionally-aware orchestration runtime.

## Core Doctrine

The Spine is authoritative.

The Pub Manager is declarative, not operational.

Jeremy Cricket advises emotional posture only.

Subsystems execute independently through event contracts.

## Startup

```bash
pip install -r requirements.txt
python main.py
```

## Endpoints

- `/api/spine/status`
- `/api/spine/pub-manager/status`
- `/api/spine/pub-manager/policy`

## Runtime Layers

1. Interfaces
2. EQ Signal Chain
3. Spine Orchestrator
4. Hub/Event Bus
5. Establishment Governance
6. Operational Subsystems
7. Persistence
```

