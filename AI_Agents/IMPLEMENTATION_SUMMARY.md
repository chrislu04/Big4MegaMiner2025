# Implementation Summary: PPO Reward System Improvements

## Changes Made to MegaMinerEnv.py

### 1. **State Tracking Variables** (in `__init__`)
Added comprehensive tracking variables for reward calculation:

```python
# Reward System State Tracking
self.tower_count_r = 0                  # Red tower count
self.tower_count_b = 0                  # Blue tower count
self.tower_count_r_prev = 0             # Previous turn count (for delta)
self.tower_count_b_prev = 0
self.enemies_killed_r = 0               # Enemy kill tracking
self.enemies_killed_b = 0
self.last_turn = 0                      # Turn tracking
self.mercenary_count_r_prev = 0         # Mercenary count tracking
self.mercenary_count_b_prev = 0
```

**Purpose:** Enable monitoring of game metrics for reward signals.

---

### 2. **Helper Methods** (added to `raw_env` class)

#### `_count_towers(team)`
Counts total towers built by a team ('r' or 'b').

#### `_calculate_tower_placement_quality(team, is_red_agent)`
Evaluates strategic tower placement based on:
- Damage-per-tile heatmap coverage
- Tower type and range
- Damage output per turn

**Returns:** Quality score (higher = better placement)

#### `_count_enemies_killed()`
Detects enemy kills by comparing entity counts.
Currently a placeholder for future enhancement.

#### `_check_invalid_action(action, agent, is_red_agent)`
Validates actions and returns appropriate penalties:
- Out-of-bounds: -0.05
- Insufficient funds: -0.10
- Occupied tile: -0.15
- Restricted tile: -0.20

#### `_is_early_game()`
Returns True if current turn < 30 (early game phase).

---

### 3. **Reset Method Updates**
Properly initializes reward system state tracking on episode reset.

---

### 4. **New Step Function** (Complete Rewrite)

The new `step()` function implements an 8-component reward system:

#### Component Ordering:
1. **Action Validity** - Immediate penalty for bad actions
2. **Early Defense** - Bonus for reaching 5-6 towers early
3. **Strategic Placement** - Bonus for high-quality tower placement
4. **Mercenary Control** - Penalty for overspending (fixes original issue!)
5. **Offensive Success** - Reward for base damage
6. **Base Protection** - Heavy penalty for defense failures
7. **Resource Efficiency** - Management of money across turns
8. **Terminal Rewards** - Win/loss outcomes

#### Key Implementation Detail - Preventing Overspending:

```python
# MERCENARY CONTROL - Penalize overspending on mercenaries
mercs_r = sum(1 for m in self.game.game_state.mercs if m.team == 'r')
if mercs_r > self.mercenary_count_r_prev:
    # Mercenary was built
    if money_r < 15:  # Critical threshold
        reward_r -= 0.2  # Penalty for overspending
```

This directly addresses the original issue: agents learn not to spend down to zero money.

#### Tower Building Reward:

```python
towers_built_r = max(0, self.tower_count_r - old_tower_count_r)
if towers_built_r > 0:
    tower_reward_r = towers_built_r * 0.2  # Base reward
    reward_r += tower_reward_r
    
    # Bonus for strategic placement
    placement_quality_r = self._calculate_tower_placement_quality('r', True)
    if placement_quality_r > 0:
        reward_r += min(0.5, placement_quality_r * 0.01)  # Capped
```

Combines base building reward with quality assessment.

#### Reward Summary for Both Players:

Both players receive symmetric rewards covering:
- Early defense bonuses (if in early game)
- Action validity penalties
- Tower construction + placement rewards
- Mercenary overspend penalties
- Base damage rewards
- Base protection penalties
- Resource efficiency tracking
- Time penalty

---

## Reward Weights Summary

| Signal | Weight | Purpose |
|--------|--------|---------|
| Early defense (5 towers) | +5.0 | Bootstrap rapid defense |
| Early defense (6 towers) | +5.0 | Continue momentum |
| Tower build | +0.2 per tower | Reward construction |
| Placement quality | +0.01 per point (capped 0.5) | Strategic placement |
| Base damage dealt | +0.5 per HP | Offensive reward |
| Base damage taken | -1.0 per HP | Defense priority |
| Income (money gain) | +0.05 per coin | Passive reward |
| Money loss without towers | -0.1 per coin | Efficiency penalty |
| Mercenary overspend | -0.2 per purchase | **Prevents original issue** |
| Invalid actions | -0.05 to -0.2 | Action validity |
| Time penalty | -0.01 per turn | Speed incentive |
| Victory | +100.0 | Win condition |
| Defeat | -100.0 | Loss condition |

---

## Problem Addressed: Overspending Fix

### Original Problem:
> "The current reward implementation results in unwanted behavior: overspending on mercenaries and ending with no money."

### Root Cause:
No penalty for spending down to zero money. Mercenary rewards outweighed resource management costs.

### Solution Implemented:
```python
# Direct check for mercenary spending with reserve constraint
if money_r < 15 and mercenary_just_bought:
    reward_r -= 0.2  # Penalty that accumulates if pattern repeats
```

Combined with:
- Money loss penalty for passive spending
- Income reward is small (0.05) to not incentivize excessive building
- Money threshold (15) is above minimum tower cost (8-10)

### Expected Behavior:
- Agent learns to maintain money reserve ≥ 15
- Still buys mercenaries strategically
- Avoids zero-money situations
- Balances offense (mercenaries) and defense (towers)

---

## Configuration for Different Playstyles

### Defensive Meta (High Tower Focus)
```python
# Increase tower rewards
tower_reward = 0.2 * 1.5  # 30% boost
# Decrease mercenary threshold
MERCENARY_OVERSPEND_THRESHOLD = 10  # Tighter control
# Increase base damage penalty
reward -= damage_taken * 1.5  # Was 1.0
```

### Balanced Meta
```python
# Default configuration is balanced
# Tweak offensive weight slightly
base_damage_multiplier = 0.5  # Keep as-is
```

### Aggressive Meta (Early Offense)
```python
# Increase base damage reward
base_damage_multiplier = 0.7  # Was 0.5
# Increase mercenary spending threshold
MERCENARY_OVERSPEND_THRESHOLD = 20  # More lenient
# Decrease early defense bonus
early_defense_bonus = 3.0  # Was 5.0
```

---

## Testing & Validation

### Test 1: Money Management (Fixes Original Issue)
```
Expected behavior:
- Turn 1-10: Builds houses for income
- Turn 10-30: Builds 5-6 towers, maintains money > 15
- Turn 30+: Strategically buys mercenaries or towers
- Never reaches 0 money involuntarily
```

### Test 2: Tower Building
```
Expected behavior:
- Reaches 5+ towers by turn 20-25
- Places towers in strategic locations
- Diversifies tower types
```

### Test 3: Combat Effectiveness
```
Expected behavior:
- Defends against early demon waves
- Gradually damages opponent base
- Wins > 70% against random policy by step 100k
```

---

## Monitoring During Training

### Key Metrics to Watch (TensorBoard)

1. **`rollout/ep_reward_mean`** - Overall episode reward
   - Should increase over time
   - Plateaus around 20-50 for balanced games

2. **`rollout/ep_len_mean`** - Average episode length
   - Long games (300 turns) = balanced play
   - Short games (50 turns) = one player dominant

3. **Custom metric to add: Money at end**
   ```python
   # In step() function, track final money
   self.infos[agent]['final_money'] = money
   # Should not reach 0
   ```

4. **Custom metric to add: Tower count at turn 30**
   ```python
   if Constants.MAX_TURNS - turns_remaining == 30:
       self.infos[agent]['towers_at_30'] = self.tower_count_r
       # Should be ≥ 5
   ```

---

## Files Modified

- **`AI_Agents/MegaMinerEnv.py`** - Complete reward system overhaul
- **`AI_Agents/REWARD_SYSTEM_GUIDE.md`** - Comprehensive documentation (NEW)

## Files Unchanged (for reference)

- `AI_Agents/train_ppo.py` - No changes needed, uses MegaMinerEnv
- `backend/` - No changes to game logic
- `rules/` - No changes to rules

---

## Next Steps for Optimization

### Phase 1: Verify Fix Works
1. Run training for 10,000 steps
2. Check that agent maintains money > 15
3. Verify tower building in early game

### Phase 2: Fine-tune Parameters
1. If overspending still occurs: increase threshold or penalty
2. If agent is too passive: decrease money loss penalty
3. If placement ignored: increase placement quality weight

### Phase 3: Add Advanced Features
1. Implement enemy kill attribution
2. Add choke-point detection
3. Tower type specialization bonuses
4. Dynamic weight adjustment based on game state

### Phase 4: Production Training
Run full training with:
- Multiple maps (map0.json - map6.json)
- Extended time (24+ hours)
- Regular checkpoints every 50,000 steps

---

## Questions & Debugging

**Q: Why is money threshold 15?**
A: Minimum tower costs are 8-10 (house, crossbow). Threshold of 15 ensures agent can build a tower if needed.

**Q: Why are early defense bonuses so high (5.0)?**
A: Early game is critical for defense establishment. High bonuses help the agent prioritize this during exploration phase.

**Q: What if agent still overspends?**
A: Increase threshold to 20-25, or increase penalty to -0.5. Monitor and adjust based on training curves.

**Q: Can I use different weights for different phases?**
A: Yes! Implement phase detection and adjust weights accordingly. See "Advanced Customization" in REWARD_SYSTEM_GUIDE.md.

**Q: How do I verify the rewards are working?**
A: Log rewards per component in step() function, analyze with TensorBoard. See "Monitoring During Training" section.

---

## Support & References

- Full reward system documentation: `REWARD_SYSTEM_GUIDE.md`
- Game logic: `backend/Game.py`
- Game rules: `rules/README.md`
- Constants: `backend/Constants.py`
