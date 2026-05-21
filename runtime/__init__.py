"""
Friday Runtime Core - Authoritative avatar state management system.

This module contains the core runtime authority layer that:
- Owns all avatar state
- Processes all commands
- Manages the tick loop
- Emits events to consumers
- Enforces the single-writer rule

No system bypasses FridayRuntimeCore. All state writes go through it.
All state reads (for choreography, etc.) go through getAvatarState().
"""

from .core import FridayRuntimeCore

__all__ = ["FridayRuntimeCore"]
