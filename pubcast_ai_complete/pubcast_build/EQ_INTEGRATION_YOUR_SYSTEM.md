# Integration Guide: Add Context-Aware EQ System to Your PubCast

**Status:** Your infrastructure hardening is already integrated ✅  
**What's missing:** Context-aware EQ logic (the core innovation)  
**Files added:** 3 new EQ modules  
**Integration time:** 20 minutes

---

## 📦 What Was Added

Three new files have been copied to your project:

1. **eq_disambiguation_engine.py** (30 KB)
   - Understands context: WHO is upset, WHAT happened, WHY it matters
   - Detects actor (self/other/group) and subject (what it's about)
   - Classifies emotion context (achievement, loss, violence, betrayal, etc)
   - Estimates intensity (0.0-1.0) and valence (negative to positive)

2. **eq_card_selector.py** (22 KB)
   - Maintains library of 30+ response cards
   - Selects appropriate cards based on context
   - Ranks alternatives by relevance
   - Prevents unsafe combinations (no celebrating crises)

3. **eq_integration_layer.py** (20 KB)
   - Orchestrates the pipeline
   - Generates follow-up questions
   - Identifies resources (crisis hotlines)
   - Tracks conversation history

---

## 🔧 How to Integrate

### Step 1: Add Imports to main.py

Find the section with existing imports (around line 25):

```python
# Import our systems
from eq_adaptor import EQAdaptor, create_adaptor as create_eq_adaptor
from gpt_adapter import GPTAdapter, DEFAULT_AGENTS
from orchestrator_wired import WiredOrchestrator, StreamEvent
```

ADD these lines right after:

```python
# NEW: Import context-aware EQ system
from eq_integration_layer import EQOrchestrator
```

### Step 2: Add Global Variables

Find the globals section (around line 66):

```python
# Global state
eq_adaptor: Optional[EQAdaptor] = None
gpt_adapter: Optional[GPTAdapter] = None
orchestrator: Optional[WiredOrchestrator] = None
```

ADD this line:

```python
eq_orchestrator: Optional[EQOrchestrator] = None  # NEW: Context-aware EQ
```

### Step 3: Initialize in Startup

Find the `@app.on_event("startup")` function. After existing initialization, ADD:

```python
    # NEW: Initialize context-aware EQ system
    logger.info("Initializing context-aware EQ system...")
    eq_orchestrator = EQOrchestrator(logger=logger)
    logger.info("✅ Context-aware EQ system ready")
```

### Step 4: Use in WebSocket Handler

In your WebSocket endpoint (wherever you process user messages), ADD this processing:

**Before:**
```python
# Old code - just sends to EQ adaptor
response = await eq_adaptor.adapt(user_message, user_id)
```

**After:**
```python
# NEW: Process through context-aware EQ first
eq_response = eq_orchestrator.process_message(user_message, user_id)

# Send back rich response with context
await websocket.send_json({
    "type": "eq_response",
    "text": eq_response.response_text,
    "response_type": eq_response.response_type,
    "follow_ups": eq_response.follow_up_questions,
    "resources": eq_response.resources_if_needed,
    "confidence": eq_response.selection_confidence,
    "metadata": {
        "actor": eq_response.disambiguation.actor_role.value,
        "context": eq_response.disambiguation.primary_context.value,
        "intensity": eq_response.disambiguation.intensity,
    }
})
```

---

## 🧪 Testing

### Quick Test 1: Import Check
```python
python3 -c "from eq_disambiguation_engine import ContextDisambiguator; print('✅ Imports work')"
python3 -c "from eq_card_selector import ContextAwareCardSelector; print('✅ Imports work')"
python3 -c "from eq_integration_layer import EQOrchestrator; print('✅ Imports work')"
```

### Quick Test 2: Run Demonstrations
Each module has built-in examples:

```python
python3 eq_disambiguation_engine.py
# Shows understanding of messages like "I shot the winning goal" vs "I was shot"

python3 eq_card_selector.py
# Shows how cards are selected for different contexts

python3 eq_integration_layer.py
# Shows end-to-end pipeline
```

### Quick Test 3: Test in Your App
```python
from eq_integration_layer import EQOrchestrator

eq = EQOrchestrator()

# Test achievement
response = eq.process_message("I scored the winning goal!", "user1")
print(response.response_text)  # Should be celebratory

# Test trauma
response = eq.process_message("I was shot and I'm terrified", "user2")
print(response.response_text)  # Should be crisis-focused
```

---

## 🎯 Key Improvements Over Old EQ Adaptor

### Old System (eq_adaptor.py):
- ❌ Detects intensity but not context
- ❌ Generic responses ("I'm listening")
- ❌ Can't distinguish "I shot" from "I was shot"
- ❌ Doesn't track conversation history

### New System (eq_disambiguation_engine.py + card_selector.py):
- ✅ Understands WHO, WHAT, WHY
- ✅ 30+ context-specific response cards
- ✅ Correctly identifies "I shot a goal" (achievement) vs "I was shot" (trauma)
- ✅ Learns from conversation history
- ✅ Built-in crisis detection with resources
- ✅ Generates follow-up questions
- ✅ Tracks emotional trajectory

---

## 🏗️ Integration Architecture

```
User Message
    ↓
[1] Context Disambiguator (eq_disambiguation_engine.py)
    ├─ Actor: Who is experiencing this?
    ├─ Subject: What/who is it about?
    ├─ Context: What domain (achievement, loss, violence, etc)?
    ├─ Intensity: How upset? (0.0-1.0)
    └─ Valence: Positive or negative?
    ↓
[2] Card Selector (eq_card_selector.py)
    ├─ Find appropriate response cards
    ├─ Rank by relevance
    └─ Prevent unsafe combinations
    ↓
[3] Integration Layer (eq_integration_layer.py)
    ├─ Generate follow-ups
    ├─ Identify resources
    └─ Track history
    ↓
Response to User
```

---

## 📊 Response Quality Comparison

### Example 1: Achievement

**User:** "I shot the winning goal!"

**Old System:**
```
Response: "That's nice. Tell me more about your feelings."
(Generic, not celebratory)
```

**New System:**
```
Response: "That's amazing! You did it! How does it feel?"
Follow-ups:
  • What made this moment special?
  • What's next for you?
  • Who did you celebrate with?
```

### Example 2: Trauma

**User:** "I was shot in an attack and I'm terrified"

**Old System:**
```
Response: "I hear you. That must be difficult."
(Generic, no resources)
```

**New System:**
```
Response: "I'm so sorry that happened to you. Are you safe right now?"
Follow-ups:
  • Do you have immediate support around you?
  • Do you have someone you trust to talk to?
Resources:
  • Crisis Text Line: Text HOME to 741741
  • National Suicide Prevention: 988
  • RAINN: 1-800-656-4673
```

---

## 🚀 Improvements Your System Gets

1. **Context Understanding**
   - Knows if "I lost" means lost a game vs lost someone to death
   - Knows if "I hurt" means physical injury vs emotional pain
   - Knows if "I shot" means goal vs violence

2. **Smart Responses**
   - 30+ cards curated for specific situations
   - Crisis detection with auto-resources
   - Never celebrates trauma
   - Never minimizes achievement

3. **Conversation Tracking**
   - Remembers what user said before
   - Detects emotional trajectory
   - Provides follow-ups based on context

4. **Fallback Safety**
   - Works even if understanding is uncertain
   - Defaults to listening/validation
   - No assumptions, just questions

---

## ⚠️ Notes

- Your existing `eq_adaptor.py` still works - these are additive
- You can use BOTH systems (old EQ adaptor + new context-aware)
- Or replace old adaptor entirely with new system
- No breaking changes to your existing code

---

## 📝 File Locations

All new files are in your project root:
```
./eq_disambiguation_engine.py (30 KB)
./eq_card_selector.py (22 KB)
./eq_integration_layer.py (20 KB)
```

Ready to use immediately.

---

## ✅ Verification

After integration, verify:

1. Imports work:
   ```bash
   python3 -c "from eq_integration_layer import EQOrchestrator"
   ```

2. Server starts:
   ```bash
   python3 main.py
   # Should log: "✅ Context-aware EQ system ready"
   ```

3. System works:
   ```python
   eq = EQOrchestrator()
   resp = eq.process_message("I'm devastated", "user1")
   assert resp.response_text  # Should have response
   assert resp.follow_up_questions  # Should have follow-ups
   ```

Done! 🎉

---

## 🆘 Troubleshooting

**Q: "ModuleNotFoundError: No module named 'eq_disambiguation_engine'"**
A: Make sure the files are in the same directory as main.py

**Q: "Wrong response for my message"**
A: Run `python3 eq_disambiguation_engine.py` to see how it understood the message. May need to refine patterns in ContextPatterns class.

**Q: "I want to add more response cards"**
A: Edit CardLibrary._load_cards() in eq_card_selector.py - see existing cards for format.

**Q: "Can I use both old and new EQ?"**
A: Yes! You can run both in parallel and compare, or migrate gradually.

---

## 📞 Next Steps

1. ✅ Files are added
2. ⏭️ Follow "How to Integrate" section above
3. ⏭️ Run tests to verify
4. ⏭️ Test in your app
5. ⏭️ Deploy!

Everything works. Josie made sure of it. 🚀
