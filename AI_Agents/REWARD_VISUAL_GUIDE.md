# Visual Quick Reference - Reward System

## Reward Components at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                   8-COMPONENT REWARD SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1️⃣  EARLY DEFENSE          (Turns 1-30 only)                  │
│      └─ Reaching 5 towers: +5.0                                 │
│      └─ Reaching 6 towers: +5.0                                 │
│                                                                   │
│  2️⃣  ACTION VALIDITY         (Every action)                      │
│      └─ Invalid action: -0.05 to -0.20                          │
│      └─ (depends on type of violation)                          │
│                                                                   │
│  3️⃣  TOWER BUILDING          (Every tower built)                 │
│      └─ Per tower: +0.2                                         │
│      └─ Placement quality: +0.01 per point (capped 0.5)        │
│                                                                   │
│  4️⃣  MERCENARY CONTROL ⭐    (When buying mercenary)            │
│      └─ If money < 15: -0.2 (KEY FIX FOR OVERSPENDING)         │
│                                                                   │
│  5️⃣  OFFENSIVE SUCCESS       (When dealing base damage)         │
│      └─ Per HP damaged: +0.5                                    │
│                                                                   │
│  6️⃣  BASE PROTECTION         (When taking base damage)          │
│      └─ Per HP damaged: -1.0                                    │
│                                                                   │
│  7️⃣  RESOURCE EFFICIENCY     (Every turn)                       │
│      └─ Money loss (no build): -0.1 × amount                   │
│      └─ Money earned: +0.05 × amount                            │
│                                                                   │
│  8️⃣  TERMINAL REWARDS        (When game ends)                   │
│      └─ Victory: +100.0                                         │
│      └─ Defeat: -100.0                                          │
│      └─ Time penalty: -0.01 per turn                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Single-Turn Reward Example

```
Turn 25 (Red player):

ACTION: Build a cannon at strategic location
  ↓
VALIDITY CHECK: ✓ Valid (on red territory, has money)
  Action penalty: 0.0
  ↓
EARLY GAME BONUS: ✓ First reach 5 towers!
  Early defense bonus: +5.0
  ↓
TOWER BUILDING: ✓ Built 1 tower
  Tower reward: 1 × 0.2 = +0.2
  Placement quality: 8.5/10 × 0.01 = +0.085 (good choke point)
  ↓
MERCENARY CHECK: No mercenary bought
  Mercenary penalty: 0.0
  ↓
COMBAT: No damage this turn
  Damage dealt: 0.0
  Damage taken: 0.0
  ↓
RESOURCE EFFICIENCY: Spent $10 on tower, earned $2 from house
  Money delta: +2
  Income reward: +2 × 0.05 = +0.1
  ↓
TIME PENALTY: -0.01
  ↓
────────────────────────────────────
TOTAL REWARD = 5.0 + 0.2 + 0.085 + 0.1 - 0.01 = 5.375
────────────────────────────────────
```

---

## Decision Tree for Reward Calculation

```
STEP CALLED
│
├─→ Invalid Action Check
│   ├─ Out of bounds? → -0.05
│   ├─ No money? → -0.10
│   ├─ Occupied tile? → -0.15
│   └─ Restricted tile? → -0.20
│
├─→ Early Game Phase? (Turns < 30)
│   ├─ First time reaching 5 towers? → +5.0
│   └─ First time reaching 6 towers? → +5.0
│
├─→ Tower Built This Turn?
│   ├─ Base reward: +0.2 per tower
│   ├─ Placement quality:
│   │   └─ Score tower heatmap coverage
│   │   └─ Add +0.01 × quality (capped 0.5)
│   └─ Subtotal: 0.2 to 0.7 per tower
│
├─→ Mercenary Bought This Turn?
│   └─ Is money < 15? → -0.2 (PREVENTS OVERSPENDING!)
│
├─→ Combat Resolved This Turn?
│   ├─ Did we damage opponent base?
│   │   └─ Add +0.5 × damage
│   └─ Did we take base damage?
│       └─ Add -1.0 × damage
│
├─→ Money Changed This Turn?
│   ├─ Lost money & didn't build towers?
│   │   └─ Add -0.1 × money lost
│   └─ Gained money (houses)?
│       └─ Add +0.05 × money gained
│
├─→ Every Turn
│   └─ Time penalty: -0.01
│
└─→ Game Over?
    ├─ We won? → +100.0
    └─ We lost? → -100.0
```

---

## Parameter Tuning Quick Reference

| Problem | Parameter | Current | Try | Location |
|---------|-----------|---------|-----|----------|
| Overspending | Money threshold | 15 | 20 | Line 585 |
| Overspending | Overspend penalty | -0.2 | -0.5 | Line 587 |
| Not building enough | Early defense bonus | 5.0 | 10.0 | Line 566 |
| Not defending enough | Base damage penalty | -1.0 | -1.5 | Line 609 |
| Not attacking enough | Base damage reward | 0.5 | 0.7 | Line 600 |
| Too passive | Time penalty | -0.01 | -0.02 | Line 627 |
| Poor placement | Placement quality weight | 0.01 | 0.02 | Line 581 |
| Not playing early | Tower build reward | 0.2 | 0.3 | Line 575 |

---

## Reward Weight Pyramid

```
                        ┌──────────────────────┐
                        │  TERMINAL REWARDS   │
                        │  Win/Loss: ±100.0  │
                        │   (Sparse)          │
                        └──────────────────────┘
                                  △
                                 / \
                ┌───────────────────────────────────┐
                │    MAJOR DENSE REWARDS            │
                │  Base Damage: ±0.5 to ±1.0       │
                │  (Highest per-turn signals)       │
                └───────────────────────────────────┘
                          △
                         / \
                ┌───────────────────────────────────┐
                │  MEDIUM DENSE REWARDS             │
                │  Tower Building: 0.2-0.7         │
                │  Early Bonuses: ±5.0 (rare)     │
                └───────────────────────────────────┘
                          △
                         / \
        ┌──────────────────────────────────────────┐
        │  SMALL CONTINUOUS REWARDS               │
        │  Resource Mgmt: ±0.05 to ±0.1          │
        │  Time Penalty: -0.01                    │
        │  Action Validity: -0.05 to -0.20       │
        └──────────────────────────────────────────┘
```

---

## Money Management Over a Game

```
Standard Game Progression:

Turn 1-5:   Money $30 → $25 (build house)
            └─ Reward: House helps passive income

Turn 5-10:  Money $25 → $20 (build tower)
            └─ Reward: Tower protection + building bonus

Turn 10-15: Money $20 → $24 (houses generating)
            └─ Reward: Income is small (+0.05 per $)

Turn 15-20: Money $24 → $15 (build 2-3 towers)
            └─ Reward: Tower bonuses worth it

Turn 20-25: Money $15 → $20 (income continues)
            └─ Status: Healthy reserve maintained

Turn 25+:   Money $20 (stable)
            └─ Agent learns:
               - Never spend < $15
               - Build strategically
               - Balance offense/defense
               - Don't overspend on mercenaries

GOAL: Final money > 0 (was failing with old system)
```

---

## Reward Timing Diagram

```
GAME TURN EXECUTION:

1. Both agents submit actions (tower, mercenary, etc.)
   
2. PHASE 1: Mercenary purchasing
   └─ Reward: Mercenary overspend penalty if money < 15

3. PHASE 2: Tower building
   └─ Reward: Tower building bonus + placement quality

4. PHASE 3: Demon provocation
   └─ Reward: (No direct reward)

5. PHASE 4: World updates (movement, combat)
   └─ Reward: Base damage dealt/taken

6. REWARD CALCULATION (after world update):
   ├─ Accumulate all component rewards
   ├─ Check for new tower milestones
   ├─ Check resource efficiency
   ├─ Apply time penalty
   └─ Check for game over → add terminal reward

7. Next turn
```

---

## Common Reward Patterns

### Pattern 1: Healthy Game (Winning)
```
Turn 50:  +5.0 (tower milestone) +0.2 (tower) +2.5 (damage) -0.01 = +7.69
Turn 100: +0.2 (tower) +3.0 (damage) +0.05 (income) -0.01 = +3.24
Turn 150: +0.2 (tower) +5.0 (damage) +0.1 (income) -0.01 = +5.29
```

### Pattern 2: Desperate Game (Losing)
```
Turn 50:  -2.0 (damage taken) -0.1 (wasted money) -0.01 = -2.11
Turn 100: -3.0 (damage taken) +0.5 (attacking back) -0.01 = -2.51
Turn 150: -100.0 (defeat) = -100.0
```

### Pattern 3: Overspending Game (BAD - PREVENTED NOW)
```
OLD SYSTEM:
Turn 30: +5.0 (mercenary built, no reward) = 5.0
Turn 31: +5.0 (mercenary built, no reward) = 5.0
Turn 40: Money = 0, base under attack = -100 (too late!)

NEW SYSTEM:
Turn 30: -0.2 (money < 15 + merc) = -0.2 ← PREVENTS THIS!
Turn 31: -0.2 (money < 15 + merc) = -0.2 ← AGENT LEARNS
Turn 40: Money = 20, still defending = +2.0
```

---

## Integration with Training Loop

```
PPO Training Loop:

┌─────────────────────────────────────────┐
│ 1. Sample trajectories from environment │
│    - Agent takes action                 │
│    - step() called                      │
│    - Reward returned (8 components)     │
│    - Next observation provided          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 2. Collect experience for training      │
│    - State-Action-Reward-State tuples   │
│    - Compute advantage estimates        │
│    - Calculate TD targets               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 3. Update policy                        │
│    - Maximize reward signal             │
│    - PPO-specific loss function         │
│    - Gradient descent on weights        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 4. Iterate                              │
│    - Repeat with updated policy         │
│    - Reward structure guides learning   │
│    - Agent improves over time           │
└─────────────────────────────────────────┘
```

---

## Success Metrics

After training for 100,000 steps, you should see:

```
✅ Money Management
   Final money: 15-30 (never zero)
   
✅ Early Defense  
   Towers at turn 30: 5-8
   
✅ Combat Performance
   Base damage dealt per game: 50-150
   Base damage taken per game: <50
   
✅ Win Rate
   vs Random Agent: >70%
   vs Previous Version: >80%
   
✅ Game Length
   Average game length: 200-300 turns
   (Longer = more balanced)
```

---

## Debugging Visualization

If something goes wrong, check:

```
SYMPTOM: Agent spends all money by turn 30
FIX LOCATION: Line 585-587 (Mercenary control)
CHECK: Is money < 15 penalty being applied?

SYMPTOM: Agent doesn't build any towers
FIX LOCATION: Line 566 (Early defense bonus)
CHECK: Is +5.0 bonus being given at 5 towers?

SYMPTOM: Agent builds towers but they don't help
FIX LOCATION: Line 581 (Placement quality)
CHECK: Is placement quality being calculated?

SYMPTOM: Agent loses even when ahead
FIX LOCATION: Line 609 (Base damage penalty)
CHECK: Is -1.0 penalty for damage being applied?

SYMPTOM: Agent never wins
FIX LOCATION: Line 600 (Offense reward) & 609 (Defense penalty)
CHECK: Is balance correct (0.5 offense vs 1.0 defense)?
```

---

This visual guide provides quick reference for understanding, debugging, and tuning the reward system. Refer to the full documentation for deeper explanations.
