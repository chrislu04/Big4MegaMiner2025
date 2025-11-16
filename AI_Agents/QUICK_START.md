# Quick Start: Using the Improved Reward System

## Overview
Your MegaMiner PPO agent now has a comprehensive, multi-component reward system designed to:
- ✓ Encourage early tower building (5-6 towers before turn 30)
- ✓ Reward strategic tower placement based on damage coverage
- ✓ **Prevent overspending on mercenaries** (the main fix)
- ✓ Balance offense and defense
- ✓ Manage resources wisely

## Running Training

### Basic Training
```bash
cd c:\Users\Nikunj\Desktop\Code\Big4MegaMiner2025
python AI_Agents/train_ppo.py --map-path map0.json --train-minutes 60
```

### Training with Logging
```bash
python AI_Agents/train_ppo.py --enable-logging --map-path map0.json --train-minutes 120
```

### Training on Different Maps
```bash
# Train on multiple maps to improve generalization
python AI_Agents/train_ppo.py --map-path map1.json --train-minutes 60
python AI_Agents/train_ppo.py --map-path map2.json --train-minutes 60
# ... etc for map3.json through map6.json
```

## Expected Behavior After Training

### Early Game (Turns 1-30)
- Agent focuses on building houses for income
- Rapidly builds 5-6 towers by turn 25-30
- Maintains money above 15 (can always build a tower)
- **No overspending on mercenaries early**

### Mid Game (Turns 30-150)
- Strategic tower placement in choke points
- Selective mercenary purchases when ahead
- Defensive play when under pressure
- Money management improves

### Late Game (Turns 150+)
- Balanced offense/defense
- Money typically 20-50 (healthy reserve)
- Wins against standard baselines > 70%

## Troubleshooting

### Problem: Agent still overspends early
**Quick Fix:**
```python
# In MegaMinerEnv.py, line ~585, decrease threshold:
if money_r < 20:  # Changed from 15
    reward_r -= 0.5  # Increased from 0.2
```

### Problem: Agent not building enough towers
**Quick Fix:**
```python
# In MegaMinerEnv.py, line ~566, increase early game bonus:
early_defense_bonus_r = 10.0  # Changed from 5.0
```

### Problem: Agent not attacking enough
**Quick Fix:**
```python
# In MegaMinerEnv.py, line ~600, increase offense weight:
reward_r += damage_dealt_r * 0.7  # Changed from 0.5
```

### Problem: Agent loses too often to defense
**Quick Fix:**
```python
# In MegaMinerEnv.py, line ~609, increase defense priority:
reward_r -= damage_taken_r * 1.5  # Changed from 1.0
```

## Key Parameters to Tune

All rewards are in `MegaMinerEnv.py`, in the `step()` function around line 520-650.

### Early Defense Rewards (Turn 1-30)
- **Line 566:** `early_defense_bonus_r = 5.0` - Bonus per milestone
- **Line 555:** `EARLY_GAME_TURNS = 30` (in `_is_early_game()`) - Define early game

### Action Validity Penalties (Prevents learning bad behavior)
- **Line 507:** Out of bounds: `-0.05`
- **Line 514:** Insufficient funds: `-0.10`
- **Line 520:** Occupied tile: `-0.15`
- **Line 526:** Restricted tile: `-0.20`

### Tower Rewards
- **Line 575:** Base tower build reward: `* 0.2`
- **Line 581:** Placement quality weight: `* 0.01` (capped at 0.5)

### Mercenary Control (MOST IMPORTANT FIX)
- **Line 585:** Money threshold: `if money_r < 15`
- **Line 587:** Overspend penalty: `reward_r -= 0.2`
  
⚠️ **These are the critical parameters for preventing overspending!**

### Base Damage Rewards
- **Line 600:** Damage dealt multiplier: `* 0.5`
- **Line 609:** Damage taken multiplier: `* 1.0`

### Resource Efficiency
- **Line 619:** Money loss penalty: `* 0.1`
- **Line 622:** Income reward: `* 0.05`

### Terminal Rewards
- **Line 678:** Victory: `+ 100.0`
- **Line 680:** Defeat: `- 100.0`

## Monitoring Training

### View TensorBoard Logs
```bash
tensorboard --logdir training/logs
```

Then open: `http://localhost:6006`

### Key Metrics to Watch
1. **Episode Reward Mean** - Should increase over time
2. **Episode Length** - 200-300 turns = balanced play
3. **Win Rate** - Should improve from ~50% to 70%+

### Add Custom Logging
To track money at end of game, edit `step()` function:
```python
if self.game.game_state.is_game_over():
    self.infos["player_r"]['final_money'] = money_r
    self.infos["player_b"]['final_money'] = money_b
```

## File Reference

| File | Purpose | Modify If |
|------|---------|-----------|
| `MegaMinerEnv.py` | Reward system implementation | Tuning rewards |
| `train_ppo.py` | Training script | Changing hyperparameters |
| `REWARD_SYSTEM_GUIDE.md` | Detailed documentation | Need detailed explanation |
| `IMPLEMENTATION_SUMMARY.md` | Changes made | Understanding structure |

## Common Training Times

| Goal | Time | Steps |
|------|------|-------|
| Basic functionality | 5 min | 10,000 |
| Early game mastery | 15 min | 50,000 |
| Decent play | 30 min | 100,000 |
| Strong play | 60 min | 200,000 |
| Expert play | 180 min | 500,000 |

## Validation Checklist

After training, verify:

- [ ] Agent builds 5+ towers by turn 25
- [ ] Final game money > 0 (no overspending)
- [ ] Win rate > 50% on any single map
- [ ] Defense holds for at least 50 turns
- [ ] Towers placed in reasonable locations
- [ ] Mercenary purchases are strategic, not reckless

## Getting Help

1. **Unexpected behavior?** Check `REWARD_SYSTEM_GUIDE.md` → Diagnosing Training Issues
2. **Want to understand the code?** Check `IMPLEMENTATION_SUMMARY.md`
3. **Need detailed parameter explanations?** Check `REWARD_SYSTEM_GUIDE.md` → Hyperparameter Defaults
4. **Want to customize rewards?** Check `REWARD_SYSTEM_GUIDE.md` → Advanced Customization

## Next Steps After Basic Training Works

### Level 2: Multi-Map Training
```bash
# Train on all maps to improve generalization
for map in map0.json map1.json map2.json map3.json map4.json map5.json map6.json
do
    python AI_Agents/train_ppo.py --map-path $map --train-minutes 30
done
```

### Level 3: Advanced Customization
1. Add demon prioritization bonus
2. Implement tower type preferences
3. Add choke-point detection
4. Dynamic reward weight adjustment based on game state

### Level 4: Fine-tuning
1. A/B test different reward weights
2. Implement curriculum learning (easy → hard maps)
3. Add self-play training (agent vs previous versions)

## Important Notes

⚠️ **Critical for preventing overspending:**
```python
# This is the KEY FIX
if mercs_r > self.mercenary_count_r_prev:
    if money_r < 15:  # ← Threshold
        reward_r -= 0.2  # ← Penalty
```

If your agent still overspends after training, increase the threshold (15→20) or penalty (0.2→0.5).

---

**Happy training! 🚀**

Questions? See the detailed guides:
- Quick reference: This file
- Full documentation: `REWARD_SYSTEM_GUIDE.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
