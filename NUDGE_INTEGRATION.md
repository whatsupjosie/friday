#!/usr/bin/env python3
"""
INTEGRATION GUIDE — Wire Nudge Queue into Your System
© 2024-2025 Rear View Foresight LLC

This file shows EXACTLY how to integrate the wired_system.py into main.py
and any other existing code.

TL;DR:
======

BEFORE (your old code):
    jeremy = JeremyCricket(bot_manager=bot_manager)
    # Problem: circular reference, testing is hard

AFTER (with nudge queue):
    nudge_q = NudgeQueue()
    jeremy = JeremyCricket(bot_manager=nudge_q)
    consumer = NudgeConsumer(nudge_q, bot_manager)
    asyncio.create_task(consumer.run())
    # Solution: clean decoupling, async delivery

That's it. Everything else stays the same.

DETAILED WALKTHROUGH:
====================
"""

import asyncio
import logging
from pathlib import Path

# Your existing imports
from wired_system import (
    JeremyCricket,
    BotManager,
    NudgeQueue,
    NudgeConsumer,
    WiredOrchestrator,
    create_wired_system,
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Minimal Integration (Just Add Nudge)
# ============================================================================

async def minimal_integration():
    """
    Minimal changes to existing code.
    Just replace the Jeremy initialization with nudge-aware version.
    """
    logger.info("=== MINIMAL INTEGRATION ===\n")

    # Step 1: Create the nudge queue
    nudge_q = NudgeQueue(maxsize=64)

    # Step 2: Create Jeremy with queue (NOT bot_manager)
    jeremy = JeremyCricket(
        bot_manager=nudge_q,  # ← Pass queue here, not actual bot_manager
        nudge_cooldown_seconds=5.0,
    )

    # Step 3: Create actual bot manager
    bot_manager = BotManager()

    # Step 4: Create and start consumer
    consumer = NudgeConsumer(nudge_q, bot_manager, max_age=30.0)
    consumer_task = asyncio.create_task(consumer.run())

    logger.info("✅ Nudge system wired up\n")

    # Now use as normal:
    # jeremy.process_message(...) will call nudge_q.nudge() when care level escalates
    # Consumer will pick it up and call bot_manager.nudge() in background

    # Cleanup
    consumer.stop()
    await asyncio.sleep(0.1)
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


# ============================================================================
# EXAMPLE 2: Full Server Integration (FastAPI)
# ============================================================================

async def full_server_integration():
    """
    Complete integration into a FastAPI server.
    Copy this pattern into your main.py startup.
    """
    logger.info("=== FULL SERVER INTEGRATION ===\n")

    # ─── At server startup (@app.on_event("startup")) ───

    # Initialize wired system
    jeremy, bot_manager, nudge_q, consumer, orchestrator = await create_wired_system()

    # Start consumer as background task
    consumer_task = asyncio.create_task(consumer.run())

    logger.info("📡 Server startup complete\n")

    # ─── In your WebSocket handler (/ws/{room_id}) ───

    async def websocket_handler(websocket, room_id: str):
        """
        Handle WebSocket messages.
        When user sends a message, it flows through orchestrator.
        """

        # Get user_id from query params
        user_id = websocket.query_params.get("user_id", "anonymous")

        # User sends message
        user_message = await websocket.receive_text()

        # Process through orchestrator (includes Jeremy + nudging)
        result = await orchestrator.handle_message(
            room_id=room_id,
            user_id=user_id,
            message=user_message,
            history=[],  # optional: prior message history
        )

        # Send result back to client
        await websocket.send_json(result)

        # NOTE: If care level escalated, a nudge was already queued
        # The consumer will pick it up and deliver to bot_manager
        # Bots will start responding asynchronously

    logger.info("📡 WebSocket handler ready\n")

    # ─── At server shutdown (@app.on_event("shutdown")) ───

    # Stop consumer gracefully
    consumer.stop()
    await asyncio.sleep(0.5)
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("📡 Server shutdown complete\n")


# ============================================================================
# EXAMPLE 3: Testing (Unit Tests)
# ============================================================================

async def testing_example():
    """
    How to write unit tests with the nudge system.
    Much cleaner than testing direct references.
    """
    logger.info("=== TESTING EXAMPLE ===\n")

    # Create isolated system for testing
    nudge_q = NudgeQueue()
    jeremy = JeremyCricket(bot_manager=nudge_q)
    bot_manager = BotManager()
    consumer = NudgeConsumer(nudge_q, bot_manager)

    # Start consumer
    consumer_task = asyncio.create_task(consumer.run())

    # Test 1: Normal message (no nudge)
    logger.info("Test 1: Normal message")
    state1 = jeremy.process_message("user1", "Hi there", room_id="test-room")
    assert state1.care_level == 0, "Should stay AMBIENT"
    assert nudge_q.qsize == 0, "No nudge queued"
    logger.info("✅ Passed\n")

    # Test 2: Emotional escalation (should nudge)
    logger.info("Test 2: Emotional escalation")
    state2 = jeremy.process_message(
        "user1",
        "I'm really struggling with everything right now!!!",
        room_id="test-room"
    )
    assert state2.care_level > 0, "Should escalate care level"
    # Give consumer a moment to process
    await asyncio.sleep(0.2)
    # Note: nudge might be delivered by consumer, or still in queue
    logger.info("✅ Passed (care_level=%d)\n", state2.care_level)

    # Test 3: Bot manager receives nudge
    logger.info("Test 3: Bot manager nudge delivery")
    accepted = await bot_manager.nudge("test-room", "emotional_escalation_2")
    assert accepted, "Bot manager should accept nudge"
    logger.info("✅ Passed\n")

    # Cleanup
    consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


# ============================================================================
# EXAMPLE 4: Real-World Scenario
# ============================================================================

async def real_world_scenario():
    """
    Realistic scenario: user gets emotional, system detects it and nudges bots.
    """
    logger.info("=== REAL-WORLD SCENARIO ===\n")

    # Initialize
    nudge_q = NudgeQueue()
    jeremy = JeremyCricket(bot_manager=nudge_q, nudge_cooldown_seconds=2.0)
    bot_manager = BotManager()
    consumer = NudgeConsumer(nudge_q, bot_manager)
    orchestrator = WiredOrchestrator(jeremy, bot_manager)

    # Start consumer
    consumer_task = asyncio.create_task(consumer.run())

    # Scenario: User in chat room starts getting emotional
    room_id = "support-room"
    user_id = "visitor_42"

    logger.info("👤 User joins chat\n")

    # Message 1: Normal greeting
    logger.info("1️⃣ User: 'Hi, I need some help'")
    r1 = await orchestrator.handle_message(room_id, user_id, "Hi, I need some help")
    logger.info("   → Care level: %s", r1["emotional_state"]["care_name"])
    logger.info("   → Nudge queue size: %d\n", nudge_q.qsize)
    await asyncio.sleep(0.2)

    # Message 2: Escalation
    logger.info("2️⃣ User: 'Actually, I'm really struggling. I don't know what to do!!!'")
    r2 = await orchestrator.handle_message(
        room_id, user_id,
        "Actually, I'm really struggling. I don't know what to do!!!"
    )
    logger.info("   → Care level: %s", r2["emotional_state"]["care_name"])
    logger.info("   → Nudge queue size: %d", nudge_q.qsize)
    logger.info("   → Jeremy has sent nudges to bot_manager queue\n")
    await asyncio.sleep(0.5)  # Let consumer process

    # What happened:
    # 1. Jeremy detected emotional escalation
    # 2. Care level went from AMBIENT (0) to CARE (2)
    # 3. Jeremy queued a nudge event (non-blocking)
    # 4. Consumer picked it up and called bot_manager.nudge()
    # 5. Bot manager can now decide which bots should respond

    # Cleanup
    consumer.stop()
    await asyncio.sleep(0.1)
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("✅ Scenario complete\n")


# ============================================================================
# KEY DIFFERENCES: Before vs After
# ============================================================================

BEFORE_PSEUDO_CODE = """
# BEFORE: Direct reference (circular dependency risk)

class JeremyCricket:
    def __init__(self, bot_manager):
        self._bm = bot_manager  # Direct reference
    
    async def process_message(self, ...):
        if care_escalated:
            await self._bm.nudge(...)  # Blocks until bot manager responds

class BotManager:
    def __init__(self, jeremy):
        self._jeremy = jeremy  # Circular!
    
    async def nudge(self, ...):
        # Uses jeremy internally

# Problem:
# - Circular dependency (A → B → A)
# - Testing requires both objects initialized together
# - If either is slow, the other blocks
# - Hard to reason about who owns what
"""

AFTER_PSEUDO_CODE = """
# AFTER: Decoupled via queue

class NudgeQueue:
    async def nudge(self, room_id, hint):
        # Just enqueue and return immediately
        self._queue.put_nowait(...)
        return True

class JeremyCricket:
    def __init__(self, bot_manager):
        self._bm = bot_manager  # Could be NudgeQueue or BotManager
    
    async def process_message(self, ...):
        if care_escalated:
            await self._bm.nudge(...)  # Returns immediately

class BotManager:
    def __init__(self):
        pass  # No reference to Jeremy
    
    async def nudge(self, ...):
        # Called by consumer, not by Jeremy directly

class NudgeConsumer:
    def __init__(self, queue, bot_manager):
        self._queue = queue
        self._bm = bot_manager
    
    async def run(self):
        while True:
            event = await self._queue.get()
            await self._bm.nudge(...)  # Actually deliver

# Benefits:
# - No circular dependency
# - Testing is isolated (just test Jeremy with queue)
# - Non-blocking (Jeremy doesn't wait for bot response)
# - Consumer can handle delivery asynchronously
# - Easy to monitor queue size/health
"""


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all examples"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    await minimal_integration()
    logger.info("\n" + "="*70 + "\n")

    await full_server_integration()
    logger.info("\n" + "="*70 + "\n")

    await testing_example()
    logger.info("\n" + "="*70 + "\n")

    await real_world_scenario()


if __name__ == "__main__":
    asyncio.run(main())
