# MegaMiner: Game Context & RL Training Goals

## 📋 Table of Contents
1. [Game Overview](#game-overview)
2. [Game Mechanics](#game-mechanics)
3. [Entities & Units](#entities--units)
4. [Economic System](#economic-system)
5. [RL Environment Setup](#rl-environment-setup)
6. [Current Training Issues](#current-training-issues)
7. [Training Goals & Success Metrics](#training-goals--success-metrics)

---

## 🎮 Game Overview

**MegaMiner** is a **turn-based, simultaneous-move tower defense game** where two AI agents (Red and Blue) compete to destroy each other's bases while defending their own territory.

### Core Objective
- **Survive**: Prevent opponent from destroying your base
- **Attack**: Build towers and hire mercenaries to damage the opponent's base
- **Manage Resources**: Balance money spending between defense and offense
- **Win Condition**: Reduce opponent's base health to 0 before they destroy yours

### Game Duration
- **Max Turns**: ~500 turns per game
- **Average Game Length**: 50-200 turns depending on agent aggression

---

## 🎯 Game Mechanics

### 1. **Turn Structure** (Simultaneous Moves)
Each turn follows this sequence:

```
1. [SIMULTANEOUS] Both agents submit actions:
   - Build a tower or structure
   - Destroy an existing tower
   - Buy a mercenary (specify direction)
   - Do nothing

2. [GAME UPDATE] All entities act:
   - Towers shoot at enemies in range
   - Mercenaries move/attack enemies
   - Demons spawn and attack
   - Buildings provide special effects (House/Church)

3. [REWARD CALCULATION] Agents receive rewards based on:
   - Damage taken
   - Damage dealt
   - Resources spent/gained
   - Invalid actions taken

4. [NEXT TURN] Process repeats until game over
```

### 2. **Map Layout**
- **Size**: 50×50 grid (or smaller, padded to 50×50)
- **Terrain Types**:
  - `P` = Path (neutral territory, walkable)
  - `R` = Red player's territory (only red can build here)
  - `B` = Blue player's territory (only blue can build here)

### 3. **Win/Loss Conditions**
- **Win**: Reduce opponent's base health from 200 to 0
- **Loss**: Your base health reaches 0
- **Draw**: Max turns reached (unlikely with sparse rewards)

---

## 🏗️ Entities & Units

### **Towers** (Defensive/Offensive Structures)

| Tower | Cost | Health | Damage | Range | Cooldown | Special |
|-------|------|--------|--------|-------|----------|---------|
| **Crossbow** | $50 | 100 | 10 | 5 | 1 turn | Basic, cheap |
| **Cannon** | $75 | 150 | 25 | 6 | 2 turns | High damage |
| **Minigun** | $100 | 120 | 5 | 4 | 0.5 turns | Fast fire rate |
| **House** | $30 | 100 | 0 | 0 | - | Economic boost (increases income) |
| **Church** | $60 | 100 | 0 | 0 | - | Defense boost (enemy penalty) |

**Tower Mechanics:**
- Towers shoot at enemies (mercs/demons) within their range
- Only attack on cooldown basis (some towers faster than others)
- Must be built on YOUR territory
- Cannot build on occupied tiles
- Can be destroyed by opponent's actions (rare)

### **Mercenaries** (Mobile Attack Units)

| Stat | Value |
|------|-------|
| **Cost** | $10 each |
| **Health** | 50 HP |
| **Damage** | 10 per hit |
| **Speed** | 1 tile/turn |
| **Spawn Location** | Specified by direction (N, S, E, W from your base) |
| **Behavior** | Walk toward enemy base, attack when adjacent |

**Mercenary Mechanics:**
- Spawned at player's base, move toward opponent's base
- Attack opponent's towers/mercs if in adjacent tile
- Die when health reaches 0
- Can be heavily penalized if purchased without money (game prevents this)

### **Demons** (Neutral Threats)

| Stat | Value |
|------|-------|
| **Source** | Spawn periodically (DemonSpawner logic) |
| **Health** | 30 HP |
| **Damage** | 8 per hit |
| **Spawn Location** | Random on paths |
| **Behavior** | Attack nearest player base or tower |

**Demon Mechanics:**
- NOT controlled by either player
- Attack any player indiscriminately
- Can be destroyed by towers/mercs for shared benefit
- Increase difficulty over time

### **Player Base**

| Stat | Value |
|-------|-------|
| **Health** | 200 HP |
| **Cost to Build** | N/A (starts with it) |
| **Range** | N/A (no attacks) |
| **Location** | Fixed corner (Red: top-left, Blue: bottom-right) |

**Base Mechanics:**
- Fixed position, never moves
- Takes damage from mercs/demons adjacent to it
- Death = game loss
- Cannot be rebuilt

---

## 💰 Economic System

### **Money Management**
- **Starting Money**: $100 per player
- **Income Sources**:
  - Houses: +$10 per house built (stacking bonus)
  - Default: Some passive income per turn
- **Spending**:
  - Towers: $30-$100 depending on type
  - Mercenaries: $10 each
  - Structures: $30-$60 (House/Church)

### **Price Scaling**
Tower prices may increase as the game progresses (economic pressure):
- Each tower of same type built → price increases slightly
- This encourages diversity in tower types
- Forces economic trade-offs

### **Financial Penalties**
- **Money < $10**: -0.03 reward per turn (encourages spending or income building)
- **Trying to buy without funds**: -0.04 penalty
- **Building without funds**: Game prevents purchase, -0.04 penalty

---

## 🤖 RL Environment Setup

### **Observation Space** (22,450 dimensions)

The agent receives a multi-channel map + global state vector:

#### **Multi-Channel Map** (50×50×9 = 22,500 values)

| Channel | Content | Example Values |
|---------|---------|-----------------|
| 0 | Terrain type | 1=Path, 2=My Territory, 3=Enemy Territory |
| 1 | Entity type | 1=Tower, 2=Merc, 3=Demon, 4=Base |
| 2 | Health (normalized) | 0.0-1.0 (0.5 = 50% health) |
| 3 | Team affiliation | 1=Mine, -1=Enemy, 0=Neutral |
| 4 | Tower type | 1-4 (Crossbow, Cannon, Minigun, House, Church) |
| 5 | Tower cooldown | 0.0-1.0 (0=ready, 1=on cooldown) |
| 6 | Unit state | 1=Walking, 2=Attacking |
| 7 | My damage heatmap | Sum of damage/turn from my towers |
| 8 | Enemy damage heatmap | Sum of damage/turn from enemy towers |

#### **Vector Features** (10 values)
```python
[
    my_money,              # Normalized by 1000
    my_base_health,        # Normalized by 200
    opp_money,             # Normalized by 1000
    opp_base_health,       # Normalized by 200
    turns_remaining,       # Normalized by MAX_TURNS
    house_cost,            # Normalized by 1000
    crossbow_cost,         # Normalized by 1000
    cannon_cost,           # Normalized by 1000
    minigun_cost,          # Normalized by 1000
    church_cost            # Normalized by 1000
]
```

### **Action Space** (MultiDiscrete)

```python
[
    action_type,    # 0=nothing, 1=build, 2=destroy
    x,              # 0-49 (x-coordinate on map)
    y,              # 0-49 (y-coordinate on map)
    tower_type,     # 0-4 (crossbow, cannon, minigun, house, church)
    merc_direction  # 0="", 1=N, 2=S, 3=E, 4=W
]
```

**Action Decoding Example:**
- `[1, 10, 15, 0, 0]` = "Build crossbow at (10, 15), no mercenary"
- `[0, 0, 0, 0, 3]` = "Do nothing, spawn mercenary going East"
- `[2, 5, 5, 0, 0]` = "Destroy tower at (5, 5)"

### **Reward Structure** (Per Turn)

| Event | Reward | Notes |
|-------|--------|-------|
| **Take 1 HP damage** | -0.13 | Heavily penalizes getting hit |
| **Deal 1 HP damage** | +0.06 | Encourages offense |
| **Money < $10** | -0.03/turn | Encourages economic growth |
| **Build tower (valid)** | +0.10 | Encourages tower placement |
| **Build tower (invalid)** | -0.04 | Penalizes bad placement |
| **No mercenary spawned** | +0.05 | Small bonus for restraint |
| **Spawn mercenary** | -0.05 | Small penalty for spending |
| **Out of bounds action** | -0.04 | Penalizes invalid coords |
| **Destroy action** | -0.04 | Discourages destruction |
| **Game Won** | +100.0 | **Sparse reward for victory** |
| **Game Lost** | -100.0 | **Sparse penalty for loss** |

---

## ⚠️ Current Training Issues

### **Issue 1: Mercenary Spam Problem**
- **Symptom**: Agent keeps spawning mercs repeatedly, ignores building towers
- **Root Cause**: Conflicting reward signals
  - `-0.30` for NOT spawning mercs (old code)
  - `+0.05` for NOT spawning (new code)
  - `-0.05` for spawning mercs
  - Only `+0.10` for building valid towers
  
**Result**: Agent learns "mercs are cheap, towers are complicated" → spams mercs

### **Issue 2: Continuous Negative Rewards (67 iterations)**
- **Symptom**: Reward stays around -0.3 to -0.5 for entire episodes
- **Root Cause**: Reward accumulation bug
  ```python
  # WRONG:
  self.rewards["player_r"] += reward_r  # Compounds across steps!
  
  # CORRECT:
  self.rewards["player_r"] = reward_r   # Reset each step
  ```

**Result**: Step 1: -0.34, Step 2: -0.69, Step 3: -1.02 (exploding negative)

### **Issue 3: House Built Reward Bug**
- **Symptom**: Blue player doesn't get rewarded for building houses
- **Root Cause**: Line 708 rewards RED player when BLUE builds
  ```python
  if house_built_b:
      reward_r += 0.08  # WRONG! Should be reward_b
  ```

**Result**: Asymmetric training, blue learns slower

### **Issue 4: Conflicting Build Rewards**
- Agent gets +0.07 for attempting build
- Then gets +0.10 for valid build location
- Then gets +0.04 for valid location (duplicate)
- **Result**: Unclear which signal matters

---

## 🎯 Training Goals & Success Metrics

### **Phase 1: Foundation** (0-50k steps)
**Goal**: Agent learns basic game mechanics without spamming mercs

**Success Metrics:**
- ✅ Mix of positive and negative rewards (not -0.3 every step)
- ✅ Agent attempts building towers (not just mercs)
- ✅ Average episode reward > -5 (not -20)
- ✅ Both players learn symmetrically

**What We Need:**
1. Fix reward accumulation bug (= not +=)
2. Fix house built bug (reward correct player)
3. Rebalance merc vs build rewards
4. Remove conflicting signals

### **Phase 2: Strategy Learning** (50k-200k steps)
**Goal**: Agent learns balanced offensive/defensive strategy

**Success Metrics:**
- ✅ Win rate > 30% against random baseline
- ✅ Diverse tower placement (not clustered)
- ✅ Economic management (doesn't stay broke)
- ✅ Average episode reward > 0

**What We Need:**
1. More training data (longer/more games)
2. Better heuristics for tower placement (maybe add location bonuses)
3. Curriculum learning (start easy, increase difficulty)

### **Phase 3: Expert Play** (200k+ steps)
**Goal**: Agent develops sophisticated play (counterplay, resource optimization)

**Success Metrics:**
- ✅ Win rate > 60% against various opponents
- ✅ Adaptive strategy (switches between offense/defense)
- ✅ Efficient tower coverage (minimal dead zones)
- ✅ Average episode reward > 10

**What We Need:**
1. GPU training (CPU is too slow)
2. Larger network capacity (policy/value networks)
3. Self-play training (agents learn from each other)
4. Advanced reward shaping (kill bonuses, coverage rewards)

---

## 📊 Training Configuration

### **Current Setup** (`train_ppo.py`)
```python
PPO Configuration:
- Policy Network: MlpPolicy (Dense layers)
- Learning Rate: 3e-4 (adaptive)
- Batch Size: 2048 steps
- N_Epochs: 10 (updates per batch)
- Clip Range: 0.2 (PPO clipping)
- Entropy Coeff: 0.01 (exploration)
- Max Steps: 1M (1 million steps)
- Eval Frequency: Every 10k steps
```

### **Hardware**
- **Current**: CPU only (Intel-based)
- **Impact**: ~10-50 steps/sec (very slow)
- **Recommended**: GPU (50-200x faster)

### **Environment Complexity**
- **Map Size**: 50×50 (2500 tiles)
- **Possible Entities**: 100+ (towers + mercs + demons)
- **Action Space**: 3 × 50 × 50 × 5 × 5 = 187,500 possible actions/turn
- **Observation Size**: 22,450 dimensions

---

## 🚀 Next Steps

### **Immediate (This Week)**
1. ✅ Apply bug fixes (accumulation, house_built, conflicts)
2. ✅ Retrain for 100k steps with fixed rewards
3. ✅ Validate reward signals are diverse (not -0.3 every step)

### **Short Term (Next Week)**
1. Move to GPU if possible (vastly faster iteration)
2. Implement self-play training (agents train against each other)
3. Add kill/survival bonuses to reward system
4. Experiment with curriculum learning (start on easier maps)

### **Medium Term (2-4 Weeks)**
1. Implement model evaluation against rule-based baseline
2. Add advanced reward shaping (coverage scores, economic efficiency)
3. Try CNN policies instead of MLP (better spatial reasoning)
4. Analyze failure modes and add targeted rewards

### **Long Term (1+ Month)**
1. Deploy trained agents against humans
2. Iteratively improve based on play patterns
3. Explore multi-agent training (3+ players)
4. Create leaderboard system

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `MegaMinerEnv.py` | RL Environment wrapper (observation, reward, step logic) |
| `train_ppo.py` | PPO training script |
| `ppo_agent.py` | Agent policy definitions |
| `backend/Game.py` | Core game logic and turn execution |
| `backend/GameState.py` | Game state tracking |
| `backend/AIAction.py` | Action structure |
| `maps/map*.json` | Game maps (different difficulty levels) |

---

## ✅ Success Definition

**An agent is "trained well" when it:**

1. **Wins consistently** (>50% vs other trained agents)
2. **Learns diverse strategies** (doesn't spam one action type)
3. **Manages resources** (balances spending with income)
4. **Adapts to opponents** (changes strategy based on board state)
5. **Plays safely** (doesn't make obviously bad trades)
6. **Scales with skill** (improves against harder opponents)

---

**Last Updated**: November 16, 2025
**Status**: Training in progress with known issues being fixed
