use serde::ser::SerializeMap;
use serde::{Deserialize, Serialize, Serializer};
use std::collections::{HashMap, HashSet, VecDeque};
use std::fmt::{self, Display};
use std::fs::File;
use std::hash::Hash;
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::{Child, Command};
use std::sync::atomic::{AtomicU64, Ordering};

////////// GLOBAL VARIABLES //////////

static UID_COUNTER: AtomicU64 = AtomicU64::new(0);

fn generate_uid() -> u64 {
    UID_COUNTER.fetch_add(1, Ordering::Relaxed)
}

////////// CONSTANTS //////////

const INITIAL_MONEY: u32 = 3;
const HOUSE_MONEY_PRODUCED: u32 = 1;
const ENEMY_INITIAL_HP: u32 = 70;
const ENEMY_ATTACK_POWER: u32 = 10;
const MERCENARY_INITIAL_HP: u32 = 70;
const MERCENARY_ATTACK_POWER: u32 = 10;
const MERCENARY_PRICE: u32 = 3;
const ENEMY_SPAWNER_RELOAD_TURNS: u32 = 10;
const BUILDER_PRICES: [u32; 6] = [0, 4, 8, 12, 16, 20];
const PLAYER_BASE_INITIAL_HP: u32 = 200;

////////// UTILITY //////////

pub fn serialize_hashmap<K, V, S>(map: &HashMap<K, V>, serializer: S) -> Result<S::Ok, S::Error>
where
    K: Display,
    V: Serialize,
    S: Serializer,
{
    let mut map_serializer = serializer.serialize_map(Some(map.len()))?;
    for (key, value) in map {
        map_serializer.serialize_entry(&key.to_string(), value)?;
    }
    map_serializer.end()
}

fn parse_direction(direction: String, from: Position) -> Result<Position, String> {
    match direction.as_str() {
        "N" => Ok(Position {
            x: from.x,
            y: from.y - 1,
        }),
        "NE" => Ok(Position {
            x: from.x + 1,
            y: from.y - 1,
        }),
        "E" => Ok(Position {
            x: from.x + 1,
            y: from.y,
        }),
        "SE" => Ok(Position {
            x: from.x + 1,
            y: from.y + 1,
        }),
        "S" => Ok(Position {
            x: from.x,
            y: from.y + 1,
        }),
        "SW" => Ok(Position {
            x: from.x - 1,
            y: from.y + 1,
        }),
        "W" => Ok(Position {
            x: from.x - 1,
            y: from.y,
        }),
        "NW" => Ok(Position {
            x: from.x - 1,
            y: from.y - 1,
        }),
        "X" => Ok(Position {
            x: from.x,
            y: from.y,
        }),
        _ => Err(format!("Invalid direction")),
    }
}

fn compute_path_to_enemy(
    start: Position,
    floor_tiles: &HashMap<Position, FloorTile>,
    enemy_color: TeamColor,
) -> VecDeque<Position> {
    todo!()
}

////////// GAME DATA STRUCTURES //////////

#[derive(PartialEq, Eq, Hash, Clone, Copy, Serialize)]
enum TeamColor {
    Red,
    Blue,
}

#[derive(PartialEq, Eq, Hash, Serialize, Clone, Copy)] // TODO: convert enums to/from string via macro. (crate strum handles to string)
enum EntityType {
    PlayerBase,
    Enemy,
    Mercenary,
    EnemySpawner,
    Tower,
}

#[derive(PartialEq, Eq, Hash, Clone, Copy, Serialize)]
enum FloorTile {
    RedTerritory,
    BlueTerritory,
    Path,
}

#[derive(PartialEq, Eq, Hash, Clone, Copy, Serialize, Deserialize)]
struct Position {
    x: i32,
    y: i32,
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({},{})", self.x, self.y)
    }
}

#[derive(Serialize, Clone)]
struct TowerStats {
    tower_type: String,
    damage: u32,
    cost: u32,
    range: u32,
    reload_turns: u32,
    initial_hp: u32,
}

#[derive(Serialize, Clone)]
struct Tower {
    uid: u64,
    position: Position,
    stats: TowerStats,
    reload_turns_left: u32,
    team_color: TeamColor,
}

impl Tower {
    fn new(position: Position, team_color: TeamColor, tower_type: String) -> Result<Tower, String> {
        let tower_stats: Result<TowerStats, String> = match tower_type.as_str() {
            "crossbow" => Ok(TowerStats {
                tower_type: String::from("crossbow"),
                damage: 3,
                cost: 2,
                range: 2,
                reload_turns: 2,
                initial_hp: 100,
            }),
            "cannon" => Ok(TowerStats {
                tower_type: String::from("cannon"),
                damage: 20,
                cost: 5,
                range: 2,
                reload_turns: 4,
                initial_hp: 100,
            }),
            "minigun" => Ok(TowerStats {
                tower_type: String::from("minigun"),
                damage: 1,
                cost: 4,
                range: 2,
                reload_turns: 1,
                initial_hp: 100,
            }),
            "house" => Ok(TowerStats {
                tower_type: String::from("house"),
                damage: 0,
                cost: 3,
                range: 0,
                reload_turns: 6,
                initial_hp: 100,
            }),
            invalid_tower_type => Err(invalid_tower_type.to_string()),
        };
        match tower_stats {
            Ok(stats) => Ok(Tower {
                uid: generate_uid(),
                position,
                stats,
                reload_turns_left: 0,
                team_color,
            }),
            Err(invalid_tower_type) => Err(format!(
                "Attempted to create tower with invalid tower_type \"{invalid_tower_type}\""
            )),
        }
    }
}

#[derive(Serialize)]
struct PlayerBase {
    uid: u64,
    position: Position,
    hp: u32,
    mercenaries_queued: VecDeque<Position>,
    team_color: TeamColor,
}

impl PlayerBase {
    fn new(position: Position, team_color: TeamColor) -> PlayerBase {
        PlayerBase {
            uid: generate_uid(),
            position,
            hp: PLAYER_BASE_INITIAL_HP,
            mercenaries_queued: VecDeque::new(),
            team_color,
        }
    }
}

#[derive(Serialize, Clone)]
struct Mercenary {
    uid: u64,
    position: Position,
    hp: u32,
    team_color: TeamColor,
    path_to_enemy: VecDeque<Position>,
}

impl Mercenary {
    fn new(
        position: Position,
        team_color: TeamColor,
        path_to_enemy: VecDeque<Position>,
    ) -> Mercenary {
        Mercenary {
            uid: generate_uid(),
            position,
            hp: MERCENARY_INITIAL_HP,
            team_color,
            path_to_enemy,
        }
    }
}

#[derive(Serialize, Clone)]
struct Enemy {
    uid: u64,
    position: Position,
    hp: u32,
    target: TeamColor,
    path_to_target: VecDeque<Position>,
}

impl Enemy {
    fn new(position: Position, target: TeamColor, path_to_target: VecDeque<Position>) -> Enemy {
        Enemy {
            uid: generate_uid(),
            position,
            hp: ENEMY_INITIAL_HP,
            target,
            path_to_target,
        }
    }
}

#[derive(Serialize, Clone)]
struct EnemySpawner {
    uid: u64,
    position: Position,
    reload_time_left: u32,
    enemies_queued: u32,
    target: TeamColor,
    switch_target: bool,
}

impl EnemySpawner {
    fn new(position: Position, target: TeamColor, switch_target: bool) -> EnemySpawner {
        EnemySpawner {
            uid: generate_uid(),
            position,
            reload_time_left: ENEMY_SPAWNER_RELOAD_TURNS,
            enemies_queued: 0,
            target,
            switch_target,
        }
    }
}

#[derive(Serialize)]
struct PlayerState {
    team_color: TeamColor,
    team_name: String,
    builder_count: u32,
    money: u32,
    mercenaries: HashMap<EntityKey, Mercenary>,
    mercenary_path: HashMap<Position, String>,
    towers: HashMap<EntityKey, Tower>,
    base: Option<PlayerBase>,
}

impl PlayerState {
    fn new(team_color: TeamColor) -> PlayerState {
        PlayerState {
            team_color,
            team_name: String::from("NO TEAM NAME SET"),
            builder_count: 1,
            money: INITIAL_MONEY,
            mercenaries: HashMap::new(),
            mercenary_path: HashMap::new(),
            towers: HashMap::new(),
            base: None,
        }
    }
}

#[derive(Hash, Serialize, PartialEq, Eq, Clone, Copy)]
struct EntityKey {
    uid: u64,
    entity_type: EntityType,
}

#[derive(Serialize)]
struct GameState {
    turns_progressed: u32,
    victory: Option<TeamColor>,
    player_state_red: PlayerState,
    player_state_blue: PlayerState,
    floor_tiles: HashMap<Position, FloorTile>,
    entity_position: HashMap<Position, EntityKey>,
    enemies: HashMap<EntityKey, Enemy>,
    enemy_spawners: HashMap<EntityKey, EnemySpawner>,
}

impl GameState {
    fn new(map_file_path: String) -> GameState {
        let mut new_game_state = GameState {
            turns_progressed: 0,
            victory: None,
            player_state_red: PlayerState::new(TeamColor::Red),
            player_state_blue: PlayerState::new(TeamColor::Blue),
            floor_tiles: HashMap::new(),
            entity_position: HashMap::new(),
            enemies: HashMap::new(),
            enemy_spawners: HashMap::new(),
        };
        // TODO: load map file stuff
        todo!()
    }

    // Use the following functions to maintain correct positions in entity_position

    fn add_tower(&mut self, tower_type: String, position: Position, team_color: TeamColor) -> () {}

    fn remove_tower(&mut self, key: EntityKey) -> () {}

    fn add_enemy_spawner(&mut self, position: Position) -> () {}

    fn remove_enemy_spawner(&mut self, key: EntityKey) -> () {}

    fn add_mercenary(&mut self, team_color: TeamColor, position: Position) -> () {}

    fn move_mercenary(&mut self, mercenary: Mercenary, new_pos: Position) -> () {}

    fn remove_mercenary(&mut self, key: EntityKey) -> () {}

    fn add_enemy(&mut self, position: Position) -> () {}

    fn move_enemy(&mut self, enemy: Enemy, new_pos: Position) -> () {}

    fn remove_enemy(&mut self, key: EntityKey) -> () {}
}

////////// PLAYER ACTIONS + VALIDATION //////////

fn try_set_team_name(
    game_state: &mut GameState,
    team_color: TeamColor,
    team_name: String,
) -> Result<(), String> {
    todo!()
}

fn try_buy_builder(game_state: &mut GameState, team_color: TeamColor) -> Result<(), String> {
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };
    match BUILDER_PRICES.get(player_state.builder_count as usize) {
        Some(&price) => match player_state.money >= price {
            true => Ok({
                player_state.builder_count += 1;
                player_state.money -= price;
            }),
            false => Err(format!(
                "The next builder costs ${}. You only have ${}",
                price, player_state.money
            )),
        },
        None => Err(format!(
            "The maximum number of builders per player is {}. You can't buy another one.",
            BUILDER_PRICES.len()
        )),
    }
}

#[derive(Deserialize)]
struct BuilderAction {
    action_type: String,
    target_x: Option<i32>,
    target_y: Option<i32>,
    tower_type: Option<String>,
}

fn try_perform_builder_action(
    game_state: &mut GameState,
    builder_action: BuilderAction,
    team_color: TeamColor,
) -> Result<(), String> {
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };
    match builder_action.action_type.as_str() {
        "build" => match (builder_action.target_x, builder_action.target_y) {
            (Some(x), Some(y)) => match game_state.floor_tiles.get(&Position { x, y }) {
                Some(tile) => match (tile, team_color) {
                    (FloorTile::RedTerritory, TeamColor::Red)
                    | (FloorTile::BlueTerritory, TeamColor::Blue) => match game_state
                        .entity_position
                        .get(&Position { x, y })
                    {
                        None => match builder_action.tower_type {
                            Some(tow_type) => {
                                match Tower::new(Position { x, y }, team_color, tow_type.clone()) {
                                    Ok(new_tower) => {
                                        match player_state.money >= new_tower.stats.cost {
                                            true => Ok({
                                                player_state.money -= new_tower.stats.cost;
                                                game_state.add_tower(
                                                    tow_type,
                                                    Position { x, y },
                                                    team_color,
                                                );
                                            }),
                                            false => Err(format!(
                                                "You're too poor to build the \"{}\" tower, which costs ${}. You only have ${}",
                                                new_tower.stats.tower_type,
                                                new_tower.stats.cost,
                                                player_state.money
                                            )),
                                        }
                                    }
                                    Err(e_str) => Err(e_str),
                                }
                            }
                            None => Err(format!(
                                "Builder action_type was \"build\", but no tower type was specified"
                            )),
                        },
                        Some(_) => Err(format!(
                            "There was already something at the target position ({},{})",
                            x, y
                        )),
                    },

                    _ => Err(format!(
                        "Builder attempted to build outside its team's territory"
                    )),
                },
                None => Err(format!(
                    "Builder attempted to build somewhere out-of-bounds"
                )),
            },
            (None, None) => Err(format!(
                "Builder action_type was \"build\", but no target position was specified"
            )),
            (None, Some(_)) => Err(format!(
                "Builder action_type was \"build\", but no target x position was specified"
            )),
            (Some(_), None) => Err(format!(
                "Builder action_type was \"build\", but no target y position was specified"
            )),
        },
        "recycle_tower" => match (builder_action.target_x, builder_action.target_y) {
            (Some(x), Some(y)) => match game_state.floor_tiles.get(&Position { x, y }) {
                Some(tile) => match (tile, team_color) {
                    (FloorTile::RedTerritory, TeamColor::Red)
                    | (FloorTile::BlueTerritory, TeamColor::Blue) => {
                        match game_state.entity_position.get(&Position { x, y }).copied() {
                            Some(entity_key) => match entity_key.entity_type {
                                EntityType::Tower => match player_state.towers.get(&entity_key) {
                                    Some(tower) => Ok({
                                        player_state.money += tower.stats.cost / 2;
                                        game_state.remove_tower(entity_key);
                                    }),
                                    None => Err(format!(
                                        "Dangling reference to tower with UID {} in entity lookup",
                                        entity_key.uid
                                    )),
                                },
                                _ => Err(format!(
                                    "There is no tower to recycle at position ({},{})",
                                    x, y
                                )),
                            },
                            None => Err(format!(
                                "There is nothing to recycle at position ({},{})",
                                x, y
                            )),
                        }
                    }
                    _ => Err(format!(
                        "Builder attempted to recycle a tower outside its team's territory"
                    )),
                },
                None => Err(format!(
                    "Builder attempted to recycle a tower somewhere out-of-bounds"
                )),
            },
            (None, None) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target position was specified"
            )),
            (None, Some(_)) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target x position was specified"
            )),
            (Some(_), None) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target y position was specified"
            )),
        },
        "nothing" => Ok(()),
        invalid => Err(format!("Builder action_type \"{invalid}\" is invalid",)),
    }
}

fn try_queue_mercenary(
    game_state: &mut GameState,
    oct_direction: String,
    team_color: TeamColor,
) -> Result<(), String> {
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };
    match &mut player_state.base {
        Some(player_base) => match parse_direction(oct_direction, player_base.position) {
            Ok(new_pos) => match game_state.floor_tiles.get(&new_pos) {
                Some(floor_tile) => match floor_tile {
                    FloorTile::Path => match player_state.money >= MERCENARY_PRICE {
                        true => Ok({
                            player_state.money -= MERCENARY_PRICE;
                            player_base.mercenaries_queued.push_back(new_pos);
                        }),
                        false => Err(format!(
                            "You're too poor to buy a mercenary. Mercenaries cost ${}. You only have ${}.",
                            MERCENARY_PRICE, player_state.money
                        )),
                    },
                    _ => Err(format!("Mercenary must start on a path tile")),
                },
                None => Err(format!("Mercenary can't go out-of-bounds")),
            },
            Err(e_str) => Err(e_str),
        },
        None => Err(format!(
            "Player base does not exist, cannot queue mercenary"
        )),
    }
}

////////// WORLD UPDATE //////////

fn move_mercenaries(game_state: &mut GameState) -> () {
    let red_desired_positions: HashSet<Position> = HashSet::new();
    for red_merc in game_state.player_state_red.mercenaries.values() {
        match game_state
            .player_state_red
            .mercenary_path
            .get(&red_merc.position)
        {
            Some(direction) => match direction {
                _ => eprintln!(
                    "THIS LINE SHOULD NEVER BE REACHED. MERCENARY PATH HAS INVALID DIRECTION"
                ),
            },
            None => eprintln!("THIS LINE SHOULD NEVER BE REACHED. MERCENARY GOT LOST!"),
        }
    }
}

fn pop_mercenaries(game_state: &mut GameState) -> () {
    todo!()
}

fn move_enemies(game_state: &mut GameState) -> () {
    todo!()
}

fn pop_enemies(game_state: &mut GameState) -> () {
    todo!()
}

fn mercenaries_attack(game_state: &mut GameState) -> () {
    todo!()
}

fn enemies_attack(game_state: &mut GameState) -> () {
    todo!()
}

fn towers_attack(game_state: &mut GameState) -> () {
    todo!()
}

////////// CORE GAME LOOP //////////

fn init_phase(agent_proc: Child, game_state: &mut GameState) -> () {
    todo!() // set team names, inform agents of their team colors
}

fn builder_shop_phase(agent_proc: Child, game_state: &mut GameState) -> () {
    todo!()
}

fn tower_shop_phase(agent_proc: Child, game_state: &mut GameState) -> () {
    todo!()
}

fn mercenary_shop_phase(agent_proc: Child, game_state: &mut GameState) -> () {
    todo!()
}

fn world_update_phase(agent_proc: Child, game_state: &mut GameState) -> () {
    todo!()
}

fn get_agent_processes(script_path: String) -> Child {
    match cfg!(windows) {
        true => match Command::new("python3").arg(script_path).spawn() {
            Ok(child) => child,
            Err(_) => panic!("Couldn't create windows subprocess for agent!"),
        },
        false => match Command::new("python3").arg(script_path).uid(65534).spawn() {
            Ok(child) => child,
            Err(_) => panic!("Couldn't create windows subprocess for agent!"),
        },
    }
}

fn main() {
    let visualizer_output_filepath = Path::new("visualizer.out");
    let mut visualizer_output_file = match File::create(&visualizer_output_filepath) {
        Err(why) => panic!("couldn't create visualizer output file: {}", why),
        Ok(file) => file,
    };
}
