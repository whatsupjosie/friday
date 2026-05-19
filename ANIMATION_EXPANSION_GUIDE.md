# Animation System Expansion Guide
**Date:** May 8, 2026  
**Status:** Ready for integration  
**Files:** `animation_presets_complete.py` + `animation_presets_complete.js`

---

## Overview

You now have **35 naturalistic, performative animations** organized into 5 categories:

| Category | Count | Use Case |
|----------|-------|----------|
| **Listening & Presence** | 9 | Active conversation (nods, leans, head tilts, weight shifts) |
| **Hand Gestures & Expression** | 8 | Speaking/emphasis (pointing, presenting, hand positions) |
| **Micro-Interactions & Fidgets** | 7 | Fill dead air naturally (collar adjust, hair, tapping, face touch) |
| **Seated Interactions** | 6 | Podcast/interview context (pivots, leans, leg cross, reaches) |
| **Emotional/Attitudinal Overlays** | 5 | Color base animations (confident, thoughtful, relaxed, skeptical) |

**All animations are:**
- ✓ Naturalistic (no slapstick, believable for a podcast host)
- ✓ Performative (convey intent and body language)
- ✓ Blendable (can layer without visual conflict)
- ✓ Context-aware (specific to seated vs standing)

---

## What's Inside

### `animation_presets_complete.py`
Drop-in replacement for your existing `animation_presets.py`.

**Key features:**
- 35 `AnimationPreset` objects, fully defined with keyframes
- `AnimationCategory` enum (LISTENING, GESTURE, FIDGET, SEATED, EMOTIONAL)
- Utility functions:
  - `get_animation(animation_id)` — retrieve by ID
  - `get_animations_by_category(category)` — filter by type
  - `get_animations_by_tag(tag)` — search by semantic tag
  - `get_loopable_animations()` — safe for continuous playback
  - `get_animations_for_context(context)` — context-aware retrieval
  - `list_all_animations()` — metadata dump for UI/debugging

**Validation:**
```
Loaded 35 animations
  gesture        :  8 animations (1 loopable)
  listening      :  9 animations (2 loopable)
  seated         :  6 animations (0 loopable)
  fidget         :  7 animations (2 loopable)
  emotional      :  5 animations (5 loopable)

Categories by context:
  seated      : 13 animations
  standing    : 15 animations
  listening   :  7 animations
  speaking    : 10 animations
  thinking    :  9 animations
```

### `animation_presets_complete.js`
Client-side mirror of the Python library.

**Exports:**
- `AnimationCategory` — enums
- `ANIMATION_LIBRARY` — full library object
- `getAnimation(id)` — lookup
- `getAnimationsByCategory(category)` — filter
- `getAnimationsByTag(tag)` — search
- `getLoopableAnimations()` — loopable filter
- `getAnimationsForContext(context)` — context filter
- `listAllAnimations()` — metadata

Works in Node.js (with `module.exports`) and browsers (with `window.PubcastAnimations`).

---

## Integration Checklist

### Step 1: Replace Python Presets
```bash
# Backup your current file
cp animation_presets.py animation_presets.py.backup_20260508

# Copy new version into place
cp animation_presets_complete.py animation_presets.py
```

### Step 2: Update Imports (if needed)
Your existing code probably imports like:
```python
from animation_presets import AnimationCategory, get_animation
```

This still works—**no changes required**. The new file is a strict superset.

### Step 3: Replace JavaScript Presets
```bash
# Backup
cp animation_presets.js animation_presets.js.backup_20260508

# Copy new version
cp animation_presets_complete.js animation_presets.js
```

### Step 4: Test
```bash
# Python
python -m pytest tests/test_spine_runtime.py -v

# JavaScript
node --check animation_presets.js

# Python syntax
python -m compileall animation_presets.py
```

### Step 5: Update Animation Runtime
If your `animation_runtime.py` or `animation_runtime.js` has hardcoded animation lists, remove them and use:

**Python:**
```python
from animation_presets import ANIMATION_LIBRARY, get_animations_for_context

# Get seated animations for podcast context
podcast_anims = get_animations_for_context("seated")
```

**JavaScript:**
```javascript
import { ANIMATION_LIBRARY, getAnimationsForContext } from './animation_presets.js';

// Get seated animations for podcast context
const podcastAnims = getAnimationsForContext("seated");
```

---

## Animation Reference by Category

### Listening & Presence (9)
Use these during active listening/conversation to show engagement and presence.

| Animation ID | Duration | Loopable | Description |
|---|---|---|---|
| `nod_slow` | 1500ms | ✓ | Thoughtful agreement nod |
| `nod_emphatic` | 800ms | ✓ | Quick emphatic nod (strong agreement) |
| `head_shake` | 1200ms | ✗ | Head shake (disagreement) |
| `head_tilt_left` | 400ms | ✗ | Curious head tilt left |
| `head_tilt_right` | 400ms | ✗ | Curious head tilt right |
| `lean_forward` | 800ms | ✗ | Lean forward (engagement) |
| `lean_back` | 800ms | ✗ | Lean back (skepticism/relax) |
| `weight_shift_left` | 600ms | ✗ | Weight shift to left leg |
| `weight_shift_right` | 600ms | ✗ | Weight shift to right leg |

**Usage:**
```python
# During conversation, randomly intersperse these
listening_anims = get_animations_by_tag("listening")
anim = random.choice(list(listening_anims.values()))
play_animation(avatar, anim.animation_id)
```

### Hand Gestures & Expression (8)
Use while avatar is speaking or emphasizing.

| Animation ID | Duration | Loopable | Description |
|---|---|---|---|
| `shoulder_shrug` | 900ms | ✗ | Shoulder shrug (uncertainty) |
| `hands_together_chest` | 600ms | ✗ | Hands clasped at chest |
| `open_palm_presentation` | 1000ms | ✓ | Palms-up presenting gesture |
| `hand_to_chin` | 700ms | ✗ | Thinking pose |
| `hands_on_hips` | 800ms | ✗ | Hands on hips (confident) |
| `hands_cross_chest` | 600ms | ✗ | Arms crossed (defensive) |
| `pointing_gesture` | 800ms | ✗ | Pointing gesture |
| `hand_wave` | 1200ms | ✗ | Friendly hand wave |

**Usage:**
```python
# During speech, use emphatic gestures
speaking_anims = get_animations_for_context("speaking")
anim = random.choice(list(speaking_anims.values()))
```

### Micro-Interactions & Fidgets (7)
Use to fill pauses and avoid dead air. These are short, non-blocking.

| Animation ID | Duration | Loopable | Description |
|---|---|---|---|
| `adjust_collar` | 1200ms | ✗ | Quick collar adjustment |
| `smooth_hair` | 1000ms | ✗ | Hair smooth gesture |
| `clasp_hands_relax` | 800ms | ✓ | Hands clasped in lap |
| `finger_tap` | 500ms | ✓ | Finger tapping rhythm |
| `glance_down` | 600ms | ✗ | Brief glance downward |
| `touch_face` | 800ms | ✗ | Touch face (thinking fidget) |
| `adjust_seat` | 800ms | ✗ | Reposition in seat |

**Usage:**
```python
# Randomly sprinkle during idle/thinking moments
fidgets = get_animations_by_tag("fidget")
anim = random.choice(list(fidgets.values()))
```

### Seated Interactions (6)
Podcast/interview-specific. These work only while seated.

| Animation ID | Duration | Loopable | Description |
|---|---|---|---|
| `lean_left_seated` | 700ms | ✗ | Lean left while seated |
| `lean_right_seated` | 700ms | ✗ | Lean right while seated |
| `pivot_torso_left` | 900ms | ✗ | Rotate torso left |
| `pivot_torso_right` | 900ms | ✗ | Rotate torso right |
| `sit_cross_legs` | 1200ms | ✗ | Cross legs (posture change) |
| `reach_forward_seated` | 900ms | ✗ | Reach forward on table |

**Usage:**
```python
# During podcast, use seated animations
if avatar.is_seated:
    seated_anims = get_animations_for_context("seated")
    anim = random.choice(list(seated_anims.values()))
```

### Emotional/Attitudinal Overlays (5)
These color base animations with attitude. Often loopable and blendable.

| Animation ID | Duration | Loopable | Description |
|---|---|---|---|
| `confident_stance` | 2000ms | ✓ | Confident upright posture |
| `thoughtful_idle` | 1500ms | ✓ | Thoughtful, introspective |
| `skeptical_expression` | 1000ms | ✓ | Skeptical raised-brow look |
| `enthusiasm_bounce` | 1200ms | ✓ | Subtle upward energy bounce |
| `relaxed_idle` | 2000ms | ✓ | Relaxed, casual posture |

**Usage:**
```python
# Layer emotional state on top of idle
confident_overlay = get_animation("confident_stance")
blend_animations(avatar, ["idle_stand"], [confident_overlay], weight=0.3)
```

---

## Runtime Integration Patterns

### Pattern 1: Active Listening (Podcast Setting)

```python
def podcast_listening_behavior(avatar):
    """Avatar listens actively while another avatar speaks."""
    listening_anims = get_animations_for_context("listening")
    
    # Randomly play listening animations
    while other_avatar.is_speaking:
        anim = random.choice(list(listening_anims.values()))
        play_animation(avatar, anim.animation_id, duration=anim.duration_ms)
        time.sleep(anim.duration_ms / 1000 + random.uniform(1, 3))  # pause between
```

### Pattern 2: Speaking with Emphasis

```python
def speaking_behavior(avatar, transcript):
    """Avatar speaks and gestures naturally."""
    speaking_anims = get_animations_for_context("speaking")
    
    for phrase in transcript.split("."):
        # Play speech
        play_audio(avatar, phrase)
        
        # Intersperse gestures
        if random.random() < 0.4:  # 40% chance of gesture
            anim = random.choice(list(speaking_anims.values()))
            play_animation(avatar, anim.animation_id, duration=anim.duration_ms)
```

### Pattern 3: Idle with Attitude

```python
def idle_with_attitude(avatar, attitude="thoughtful"):
    """Avatar waits with a specific emotional tone."""
    base_idle = get_animation("idle_stand")
    emotion_anim = get_animation(f"{attitude}_idle")
    
    # Play base with emotional overlay
    blend_animations(avatar, [base_idle], [emotion_anim], weight=0.4)
    
    # Sprinkle fidgets
    fidgets = get_animations_by_tag("fidget")
    while waiting:
        if random.random() < 0.2:  # Fidget 20% of the time
            fidget = random.choice(list(fidgets.values()))
            play_animation(avatar, fidget.animation_id)
```

### Pattern 4: Seated Podcast

```python
def podcast_interaction(avatar_a, avatar_b):
    """Two avatars in seated podcast conversation."""
    seated_anims = get_animations_for_context("seated")
    listening_anims = get_animations_for_context("listening")
    
    while podcast_running:
        # Avatar A speaks, Avatar B listens
        play_audio(avatar_a, script[current_line])
        
        # Avatar B reacts
        if random.random() < 0.5:
            react_anim = random.choice(list(listening_anims.values()))
            play_animation(avatar_b, react_anim.animation_id)
        
        # Occasionally avatar B shifts position
        if random.random() < 0.3:
            shift_anim = random.choice(list(seated_anims.values()))
            play_animation(avatar_b, shift_anim.animation_id)
```

---

## Context Strings (for `get_animations_for_context`)

Use these strings to get context-appropriate animation sets:

- **`"seated"`** — Sitting interaction (podcasts, interviews, meetings)
- **`"standing"`** — Standing, stationary (presentations, casual talk)
- **`"listening"`** — Active listening (nods, head tilts, agreement signals)
- **`"speaking"`** — While avatar is talking (gestures, emphasis, pointing)
- **`"thinking"`** — Contemplative moments (hand-to-chin, fidgets, introspection)

---

## Tag-Based Filtering

Every animation has a `tags` set. Use `get_animations_by_tag()` to filter by semantic intent:

**Common tags:**
- `"agreement"`, `"listening"`, `"engagement"` — Agreement/attention
- `"gesture"`, `"presentation"`, `"emphasis"` — Speaking/emphasis
- `"natural"`, `"subtle"` — Quiet, unobtrusive movements
- `"fidget"`, `"grooming"` — Micro-interactions
- `"confident"`, `"relaxed"`, `"thoughtful"` — Emotional tone
- `"seated"`, `"body"` — Body-focused animations

**Example:**
```python
# Get all confident-looking animations
confident_anims = get_animations_by_tag("confident")

# Get all thinking-related animations
thinking_anims = get_animations_by_tag("thinking")

# Get all subtle movements
subtle_anims = get_animations_by_tag("subtle")
```

---

## Blending & Overlays

Some animations are marked with `blendable_with`. Use these to layer animations:

```python
# Layer confident stance over idle_stand
base_anim = get_animation("idle_stand")
overlay_anim = get_animation("confident_stance")

# Blend at 40% intensity
avatar.blend_animation(base_anim.animation_id, overlay_anim.animation_id, weight=0.4)
```

---

## Next Steps for Further Expansion

**If you need more:**

1. **Additional emotions** — Add `happy_bounce`, `sad_slouch`, `angry_posture`
2. **Interaction sequences** — Multi-person choreography (duets, arguments, agreements)
3. **Talking variations** — Mouth sync, eye tracking, blink patterns
4. **Transitions** — Smooth blends between states (sit→stand, stand→walk)
5. **Character-specific** — Different animation sets for different avatar models

**Pattern for adding new animations:**
```python
EXAMPLE_NEW_ANIM = AnimationPreset(
    animation_id="example_id",
    category=AnimationCategory.GESTURE,
    display_name="Example Animation",
    duration_ms=800,
    is_loopable=False,
    is_blocking=False,
    frames=[
        BoneKeyframe("bone_id", 0, 0, rotation=(0, 0, 0)),
        BoneKeyframe("bone_id", 20, 800, rotation=(0, 0, 15)),
    ],
    tags={"gesture", "example", "your_tag"},
    description="Description of what this does.",
)

# Add to ANIMATION_LIBRARY
ANIMATION_LIBRARY["example_id"] = EXAMPLE_NEW_ANIM
```

---

## Troubleshooting

### Animation not playing?
1. Check animation ID is in `ANIMATION_LIBRARY`
2. Verify `is_blocking` logic—maybe another animation is still playing
3. Ensure avatar is in the right state (seated vs standing) for the animation

### Animation looks jittery/unnatural?
1. Check frame durations add up correctly
2. Verify bone IDs match your rig
3. Reduce rotation/position deltas if too extreme

### Need to disable an animation?
```python
# Remove from runtime (don't delete from library)
available_anims = get_animations_for_context("seated")
del available_anims["animation_id_to_skip"]
```

---

## Validation

Both Python and JavaScript versions are validated:

```bash
# Python
python animation_presets_complete.py
✓ Loaded 35 animations
✓ All categories populated
✓ All utility functions work

# JavaScript
node --check animation_presets_complete.js
✓ Syntax OK
```

---

## Questions?

- **Structure:** Mirrors your existing `animation_presets.py`—fully compatible
- **Duration:** All timings in milliseconds (ms)
- **Blending:** Some animations can layer via `blendable_with` set
- **Context:** Use utility functions, not hardcoded animation lists
- **Tags:** Semantic search by intent, not just category

You've got 35 animations ready to go. Drop them in and start using them.
