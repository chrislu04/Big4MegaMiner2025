# PPO Reward System Guide for MegaMiner Tower Defense

## Overview

The improved reward system in `MegaMinerEnv.py` has been redesigned to address the issue of overspending on mercenaries and to encourage consistent winning behavior. The system implements a multi-component reward structure that provides dense rewards for good decisions while penalizing poor ones.

## Reward Design Requirements & Implementation

### 1. **Action Validity** ✓
**Purpose:** Penalize all invalid actions to teach the agent proper play.

**Implementation:**
- Method: `_check_invalid_action()`
- **Out-of-bounds actions:** -0.05 penalty
- **Insufficient funds:** -0.10 penalty
- **Building on occupied tiles:** -0.15 penalty
- **Building on non-territory tiles:** -0.20 penalty

**When triggered:** Every agent step before execution

**Tuning tips:**
- Increase penalties if agent keeps trying invalid actions
- Decrease penalties if agent learns boundaries too conservatively

---

### 2. **Early Defense Construction** ✓
**Purpose:** Reward building 5–6 towers early to establish strong defense.

**Implementation:**
- Method: `_is_early_game()` - returns True for turns < 30
- **Reaching 5 towers:** +5.0 bonus
- **Reaching 6 towers:** +5.0 bonus
- Only applies in early game phase

**Key insight:** Large one-time bonuses encourage rapid tower construction without punishing normal play.

**Tuning tips:**
- Adjust turn threshold (30) based on game pacing
- Increase bonus (5.0) if agent still overspends early
- Add more milestone bonuses at 7-8 towers if desired

---

### 3. **Strategic Tower Placement** ✓
**Purpose:** Reward placing towers in high-impact locations (high heatmap values).

**Implementation:**
- Method: `_calculate_tower_placement_quality()`
- Builds damage-per-tile heatmap for each tower type
- Scores placement based on coverage of high-damage zones
- **Placement bonus:** +0.01 × quality score (capped at +0.5)

**Heatmap calculation:**
```
For each offensive tower (cannon, minigun, crossbow):
  damage_per_turn = tower_damage / tower_cooldown
  For each tile in range:
    damage_heatmap[y][x] += damage_per_turn
  placement_quality += sum(heatmap values in tower range)
```

**Tuning tips:**
- Increase cap (0.5) if agent is too conservative with towers
- Increase multiplier (0.01) for more emphasis on placement quality
- Adjust to reward specific tower types (cannons/miniguns for choke points, crossbows for range)

---

### 4. **Enemy Engagement & Prioritization** ✓
**Purpose:** Reward damaging enemy base, especially with effective towers.

**Implementation:**
- **Base damage reward:** +0.5 × damage dealt to opponent base
- Coupled with strategic placement (tower placement rewards = strategic offense)
- Demons are automatically prioritized since they're higher threat

**Note:** Enemy kill tracking is currently a placeholder. To enhance:
1. Track mercenary/demon count changes
2. Attribute kills to towers based on proximity/position
3. Add demon kill bonus: +1.0 per demon killed
4. Add mercenary kill bonus: +0.5 per mercenary killed

**Implementation example for future enhancement:**
```python
def _attribute_kills(self):
    # Track entity count changes each turn
    # Reward kills proportionally to tower placement
    # Penalize letting enemies reach base
```

---

### 5. **Base Protection** ✓
**Purpose:** Penalize damage taken; higher penalty for severe damage.

**Implementation:**
- **Scaling penalty:** -1.0 × damage taken
- Applied every turn damage occurs
- Creates strong incentive to maintain defense

**Example:**
- Take 5 damage: -5.0 reward
- Take 10 damage: -10.0 reward

**Tuning tips:**
- This should be roughly equal weight to base damage reward (0.5)
- If agent ignores base health, increase multiplier to -1.5 or -2.0
- If agent is too defensive, decrease multiplier

---

### 6. **Win/Loss Conditions** ✓
**Purpose:** Large sparse rewards for terminal outcomes.

**Implementation:**
- **Victory:** +100.0 reward
- **Defeat:** -100.0 penalty
- Applied when `game_state.is_game_over()` returns True

**Importance:** These large rewards anchor the training and provide clear success signals.

**Tuning tips:**
- Keep these large relative to per-turn rewards (100x larger)
- Experiment with different magnitudes (50, 100, 200) based on episode length
- Can add tie-breaking bonuses based on final score metrics

---

### 7. **Resource Efficiency** ✓
**Purpose:** Penalize overspending and poor resource management; reward maintaining cash reserves.

**Implementation:**
- **Mercenary overspending check:** If `mercenary_bought and money < 15`, apply -0.2 penalty
- **Passive money loss penalty:** If `money_delta < 0 and no_towers_built`, apply -0.1 × |money_lost|
- **Income reward:** If `money_delta > 0`, apply +0.05 × income

**Key mechanism (prevents the original issue):**
```python
# MERCENARY CONTROL - Penalize overspending on mercenaries
if mercs_built > 0 and money < 15:
    reward -= 0.2  # Discourages buying mercenaries without reserve
```

**Tuning tips:**
- **Money threshold (15):** Adjust based on cheapest tower cost
  - If using house (cost 10), set to 12-15
  - If wanting more conservative play, increase to 20-25
- **Mercenary penalty (-0.2):** Increase to -0.5 if overspending persists
- **Income reward (0.05):** Much smaller than base damage reward by design (passive play shouldn't win)

---

### 8. **Offensive Success** ✓
**Purpose:** Strong reward for damaging enemy base; encourages both defense and offense.

**Implementation:**
- **Base damage reward:** +0.5 × damage_to_opponent_base
- Applied every turn opponent takes damage
- Scales with damage amount

**Combined with tower rewards:** Tower placement + base damage creates natural synergy.

**Tuning tips:**
- This is intentionally strong (0.5) since dealing damage is game-winning
- If agent is too aggressive, reduce to 0.3
- If agent is too passive, increase to 0.7-1.0

---

## Reward Component Summary Table

| Component | Weight | Trigger | Benefit | Risk |
|-----------|--------|---------|---------|------|
| Early defense (5 towers) | +5.0 | Reaching 5 towers in early game | Rapid defense setup | One-time only |
| Tower building | +0.2 per tower | Each tower built | Incentivizes defense | Could be spammed |
| Placement quality | +0.01 per point | Strategic placement | Efficient defense | Weak signal |
| Base damage dealt | +0.5 per HP | Opponent takes damage | Offense encouraged | Could be reckless |
| Base damage taken | -1.0 per HP | Player takes damage | Defense critical | Could be too risk-averse |
| Money management | ±0.05 income, -0.2 merc overspend | Resource changes | Prevents overspending | Requires tuning threshold |
| Invalid action | -0.05 to -0.2 | Attempted bad action | Discourages mistakes | Early training noise |
| Time penalty | -0.01 | Every turn | Faster wins preferred | Can cause rushed play |
| Victory | +100.0 | Win game | Clear success signal | Requires winning |
| Defeat | -100.0 | Lose game | Failure signal | Strong deterrent |

---

## Training Recommendations

### Phase 1: Foundation (First 50,000 steps)
- Focus on action validity and early defense
- Use standard penalties to teach boundaries
- Agent should learn to build 5-6 towers reliably

### Phase 2: Strategic Development (50,000 - 200,000 steps)
- Tower placement quality becomes more important
- Base damage rewards encourage offense
- Watch for overspending on mercenaries
- If overspending occurs, increase money threshold from 15 to 20

### Phase 3: Refinement (200,000+ steps)
- Fine-tune weight combinations
- Observe which reward components have most impact
- Consider adding:
  - Tower type specialization bonuses
  - Path-based placement rewards (choke points)
  - Demon prioritization bonuses

---

## Diagnosing Training Issues

### Problem: Agent keeps trying invalid actions
**Solution:** Increase invalid action penalties
```python
# Current:
penalty = -0.05  # Out of bounds
# Try:
penalty = -0.10  # Out of bounds (doubled)
```

### Problem: Agent overspends on mercenaries (original issue)
**Solution:** Increase mercenary overspending penalty or lower money threshold
```python
# Current:
if money < 15:  # threshold
    reward -= 0.2  # penalty
# Try:
if money < 20:  # higher threshold
    reward -= 0.5  # higher penalty
```

### Problem: Agent builds too many towers without attacking
**Solution:** Increase base damage reward weight
```python
# Current:
reward_r += damage_dealt_r * 0.5
# Try:
reward_r += damage_dealt_r * 0.7  # increased
```

### Problem: Agent is too aggressive, ignoring defense
**Solution:** Increase base damage penalty weight
```python
# Current:
reward -= damage_taken * 1.0
# Try:
reward -= damage_taken * 1.5  # increased
```

### Problem: Agent gets stuck in local optima
**Solution:** Increase early defense bonus or adjust time penalty
```python
# Current:
early_defense_bonus = 5.0  # per milestone
# Try:
early_defense_bonus = 10.0  # doubled

# Also try:
time_penalty = -0.02  # from -0.01
```

---

## Advanced Customization

### Tower Type Preferences

To prefer specific towers (e.g., cannons and miniguns for choke points):

```python
def _calculate_tower_placement_quality(self, team, is_red_agent):
    # ... existing code ...
    placement_score = 0.0
    for t in self.game.game_state.towers:
        # ... existing code ...
        # Add type-specific bonuses:
        if t_type_upper == "CANNON":
            placement_score *= 1.5  # 50% bonus for cannons
        elif t_type_upper == "MINIGUN":
            placement_score *= 1.3  # 30% bonus for miniguns
        # Crossbows are baseline
```

### Choke Point Detection

To reward towers placed in high-traffic areas:

```python
def _is_choke_point(self, x, y):
    """Detect if position is on a main path."""
    # Count demons/mercenaries that pass through this tile
    # Reward placement on frequently-traveled tiles
```

### Dynamic Weighting

Adjust reward weights based on game state:

```python
if self._is_early_game():
    defense_weight = 1.0  # Emphasize defense
else:
    defense_weight = 0.5
    offense_weight = 1.0  # Emphasize offense late game
```

---

## Testing the Reward System

### Test 1: Valid Action Learning
- Train for 1000 steps
- Monitor invalid action attempts (should decrease)
- Expected: < 5% invalid actions by step 1000

### Test 2: Early Defense
- Train for 5000 steps
- Check if agent builds 5+ towers before turn 30
- Expected: > 80% success rate by step 5000

### Test 3: Money Management
- Train for 10000 steps
- Monitor final game money (should be > initial / 2)
- Expected: Agent maintains cash reserve

### Test 4: Win Rate
- Train for 100,000 steps
- Evaluate against random policy
- Expected: Win rate > 70% by step 100,000

---

## Hyperparameter Defaults

```python
# Early game tower bonuses
EARLY_GAME_TURNS = 30
TOWER_MILESTONE_5 = 5.0
TOWER_MILESTONE_6 = 5.0

# Action validity penalties
INVALID_OUT_OF_BOUNDS = -0.05
INVALID_INSUFFICIENT_FUNDS = -0.10
INVALID_OCCUPIED_TILE = -0.15
INVALID_RESTRICTED_TILE = -0.20

# Tower rewards
TOWER_BUILD_REWARD = 0.2
TOWER_PLACEMENT_QUALITY_MULTIPLIER = 0.01
PLACEMENT_QUALITY_CAP = 0.5

# Mercenary control
MERCENARY_OVERSPEND_THRESHOLD = 15
MERCENARY_OVERSPEND_PENALTY = -0.2

# Resource efficiency
MONEY_LOSS_MULTIPLIER = -0.1
INCOME_REWARD_MULTIPLIER = 0.05

# Combat rewards
BASE_DAMAGE_REWARD_MULTIPLIER = 0.5
BASE_DAMAGE_PENALTY_MULTIPLIER = -1.0

# Terminal rewards
VICTORY_REWARD = 100.0
DEFEAT_PENALTY = -100.0

# Time penalty
TIME_PENALTY = -0.01
```

---

## Key Insights

1. **Multi-component rewards > single reward:** Breaking down objectives helps the agent learn faster
2. **Asymmetric scaling is important:** Defense penalty (1.0) should be close to offense reward (0.5) for balanced play
3. **Thresholds matter:** Money threshold (15) directly controls overspending behavior
4. **Early bonuses accelerate learning:** Large rewards for reaching early milestones help bootstrap training
5. **Placement quality needs careful calibration:** Too weak and agent ignores it; too strong and agent wastes time optimizing

---

## References

- Original game rules: `rules/README.md`
- Game constants: `backend/Constants.py`
- Tower definitions: `backend/Cannon.py`, `backend/Minigun.py`, `backend/Crossbow.py`
- Environment code: `AI_Agents/MegaMinerEnv.py`
- Training script: `AI_Agents/train_ppo.py`
