use serde::ser::SerializeMap;
use serde::{Deserialize, Serialize, Serializer};
use serde_json::Deserializer;
use std::collections::{HashMap, HashSet, VecDeque};
use std::fmt::{self, Display};
use std::fs::File;
use std::hash::Hash;
use std::io::BufReader;
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

//
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
    from_pos: Position,
    floor_tiles: &HashMap<Position, FloorTile>,
    enemy_location: Position,
) -> Result<VecDeque<Position>, String> {
    let mut explored: HashSet<Position> = HashSet::new();
    let mut frontier: Vec<VecDeque<Position>> = Vec::new();
    frontier.push(VecDeque::from_iter([from_pos]));
    while !frontier.is_empty() {
        match frontier.pop() {
            Some(top) => match *top.back().expect("") == enemy_location {
                true => return Ok(top),
                false => {
                    for nbr in [
                        Position {
                            x: top[0].x,
                            y: top[0].y + 1,
                        },
                        Position {
                            x: top[0].x + 1,
                            y: top[0].y,
                        },
                        Position {
                            x: top[0].x,
                            y: top[0].y - 1,
                        },
                        Position {
                            x: top[0].x - 1,
                            y: top[0].y,
                        },
                    ] {
                        match (!explored.contains(&nbr)) && floor_tiles[&nbr] == FloorTile::Path {
                            true => {
                                explored.insert(nbr);
                                let mut new = top.clone();
                                new.push_back(nbr);
                                frontier.push(new);
                            }
                            false => continue,
                        }
                    }
                }
            },
            None => break,
        }
    }
    return Err("Unable to find path to enemy".to_string());
}

////////// GAME DATA STRUCTURES //////////

#[derive(PartialEq, Eq, Hash, Clone, Copy, Serialize)]
enum TeamColor {
    Red,
    Blue,
}

fn parse_team_color(string: String) -> Option<TeamColor> {
    match string.as_str() {
        "r" => Some(TeamColor::Red),
        "b" => Some(TeamColor::Blue),
        _ => None,
    }
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
    fn get_desired_position(&self) -> Position {
        match self.path_to_enemy.len() {
            0 => panic!("Shouldn't be here"),
            1 => panic!("Shouldn't be here"),
            2 => self.position,
            _ => match self.path_to_enemy.front() {
                Some(pos) => *pos,
                None => panic!("Contradiction"),
            },
        }
    }
}

#[derive(Serialize, Clone)]
struct Enemy {
    uid: u64,
    position: Position,
    hp: u32,
    path_to_target: VecDeque<Position>,
}

impl Enemy {
    fn new(position: Position, target: TeamColor, path_to_target: VecDeque<Position>) -> Enemy {
        Enemy {
            uid: generate_uid(),
            position,
            hp: ENEMY_INITIAL_HP,
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
#[derive(Deserialize)]
struct SpawnerFromMapfile {
    x: i32,
    y: i32,
    target: String,
    switch_target: bool,
}

#[derive(Deserialize)]
struct DataFromMapfile {
    floor_tiles: Vec<String>,
    red_base: Position,
    blue_base: Position,
    spawners: Vec<SpawnerFromMapfile>,
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

    // Create a new game state object from a map file
    fn new(map_file_path_str: &String) -> GameState {

        // Create the struct, and fill in all properties which don't need to come from the file
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

        // Attempt to open the map file
        match File::open(map_file_path_str) {

            // Successfully opened map file
            Ok(file) => {

                // Map file is in JSON format. Deserialize it.
                let mut de = Deserializer::from_reader(BufReader::new(file));
                match DataFromMapfile::deserialize(&mut de) {

                    // Deserialization was successful
                    Ok(data) => {

                        // Iterate through all the floor tiles in the map file
                        for (y_i, line) in data.floor_tiles.iter().enumerate() {
                            for (x_i, chr) in line.chars().enumerate() {

                                // Get the floor tile for the current iteration
                                let at_pos = match chr {
                                    'r' => Some(FloorTile::RedTerritory),
                                    'b' => Some(FloorTile::BlueTerritory),
                                    'O' => Some(FloorTile::Path),
                                    _ => None, // Invalid
                                };

                                // Was a valid floor tile specified?
                                match at_pos {

                                    // Yes. A valid floor tile was specified. Attempt to insert it into the map.
                                    Some(tile) => match new_game_state.floor_tiles.insert(
                                        Position {
                                            x: x_i as i32,
                                            y: y_i as i32,
                                        },
                                        tile,
                                    ) {

                                        // Successfully inserted the new floor tile
                                        None => (),

                                        // There was already a tile where we tried to insert the new floor tile
                                        Some(_) => eprintln!(
                                            "Error: During game map initialization: there was already a tile at position ({},{}). This line should not be reached.",
                                            x_i, y_i
                                        ),
                                    },

                                    // Invalid floor tile specification. Panic
                                    None => panic!("Invalid floor tile specified at position ({},{}).", x_i, y_i),
                                }
                            }
                        }

                        // Place the blue base
                        new_game_state.player_state_blue.base =
                            Some(PlayerBase::new(data.blue_base, TeamColor::Blue));
                        
                        // Place the red base
                        new_game_state.player_state_red.base =
                            Some(PlayerBase::new(data.red_base, TeamColor::Red));
                        
                        // Place the enemy spawners
                        for from_mapfile in data.spawners {
                            new_game_state.add_enemy_spawner(from_mapfile);
                        }
                    }

                    // Deserialization was unsuccessful. Panic
                    Err(err) => panic!("Unable to deserialize map data: {}", err.to_string()),
                }
            }

            // Unable to open map file. Panic
            Err(err) => panic!(
                "Failed to open map file {}: {}",
                map_file_path_str,
                err.to_string()
            ),
        };
        new_game_state
    }

    // Use the following functions to maintain correct positions in entity_position

    fn add_tower(&mut self, tower_type: String, position: Position, team_color: TeamColor) -> () {
        let player_state = match team_color {
            TeamColor::Red => &mut self.player_state_red,
            TeamColor::Blue => &mut self.player_state_blue,
        };
        match Tower::new(position, team_color, tower_type) {
            Ok(tower) => {
                let key = EntityKey {
                    uid: tower.uid,
                    entity_type: EntityType::Tower,
                };
                match self.entity_position.insert(tower.position, key) {
                    None => (),
                    Some(_) => panic!(
                        "Replacing an entity at position ({},{}), this line should not be reached",
                        tower.position.x, tower.position.y
                    ),
                }
                match player_state.towers.insert(key, tower) {
                    Some(_) => panic!(
                        "Replacing a tower with uid {}, this line should not be reached",
                        key.uid
                    ),
                    None => (),
                }
            }
            Err(e_str) => {
                panic!(
                    "Failed to create tower! Something is probably wrong with validation! Error was:\n{}",
                    e_str
                );
            }
        }
    }

    fn remove_tower(&mut self, key: EntityKey) -> () {
        match (
            self.player_state_blue.towers.remove(&key),
            self.player_state_red.towers.remove(&key),
        ) {
            (None, None) => panic!(
                "Tried to remove tower with uid {}, but it does not exist",
                key.uid
            ),
            (Some(_), Some(_)) => {
                panic!("Tower with uid {} belongs to both teams", key.uid);
            }
            (Some(b), None) => match self.entity_position.remove(&b.position) {
                Some(_) => (), // If you're really paranoid you can check this result and panic!
                None => panic!(
                    "Tower with uid {} exists, but is not in the entity_position map",
                    key.uid
                ),
            },
            (None, Some(r)) => match self.entity_position.remove(&r.position) {
                Some(_) => (), // If you're really paranoid you can check this result and panic!
                None => panic!(
                    "Tower with uid {} exists, but is not in the entity_position map",
                    key.uid
                ),
            },
        }
    }

    fn add_enemy_spawner(&mut self, from_map: SpawnerFromMapfile) -> () {
        match parse_team_color(from_map.target) {
            Some(tc) => {
                let new_spanwer = EnemySpawner::new(
                    Position {
                        x: from_map.x,
                        y: from_map.y,
                    },
                    tc,
                    from_map.switch_target,
                );
                let key = EntityKey {
                    uid: new_spanwer.uid,
                    entity_type: EntityType::EnemySpawner,
                };
                match self.entity_position.insert(new_spanwer.position, key) {
                    None => (),
                    Some(_) => panic!(
                        "Replacing an entity at position ({},{}), this line should not be reached",
                        new_spanwer.position.x, new_spanwer.position.y
                    ),
                }
                match self.enemy_spawners.insert(key, new_spanwer) {
                    None => (),
                    Some(_) => panic!("Duplicate enemy spawner"),
                }
            }
            None => panic!(
                "Spawner in map file targets nonexistent team. Target should be \"r\" or \"b\"."
            ),
        }
    }

    // fn remove_enemy_spawner() // don't ever need to remove spawners

    fn add_mercenary(&mut self, team_color: TeamColor, position: Position) -> () {
        let other_player_state = match team_color {
            TeamColor::Red => &mut self.player_state_blue,
            TeamColor::Blue => &mut self.player_state_red,
        };
        match &other_player_state.base {
            Some(base) => match compute_path_to_enemy(position, &self.floor_tiles, base.position) {
                Ok(path_to_enemy) => {
                    let merc = Mercenary::new(position, team_color, path_to_enemy);
                    let key = EntityKey {
                        uid: merc.uid,
                        entity_type: EntityType::Mercenary,
                    };
                    match self.entity_position.insert(merc.position, key) {
                        None => (),
                        Some(_) => panic!(
                            "Replacing an entity at position ({},{}), this line should not be reached",
                            merc.position.x, merc.position.y
                        ),
                    }
                    let player_state = match team_color {
                        TeamColor::Red => &mut self.player_state_red,
                        TeamColor::Blue => &mut self.player_state_blue,
                    };
                    match player_state.mercenaries.insert(key, merc) {
                        Some(_) => panic!(
                            "Replacing a mercenary with uid {}, this line should not be reached",
                            key.uid
                        ),
                        None => (),
                    }
                }
                Err(e_str) => panic!(
                    "Mercenary couldn't compute path to enemy. Reason: {}",
                    e_str
                ),
            },
            None => panic!(
                "Mercenary can't compute path to enemy base, because the enemy's base does not exist"
            ),
        }
    }

    fn move_mercenary(&mut self, mercenary: &mut Mercenary) -> () {
        let desired = mercenary.get_desired_position();
        if desired != mercenary.position {
            let key = EntityKey {
                uid: mercenary.uid,
                entity_type: EntityType::Mercenary,
            };
            match self.entity_position.remove(&mercenary.position) {
                Some(_) => (), // could verify here if paranoid, then panic!
                None => panic!("entity_position map is desynced"),
            }
            match self.entity_position.insert(desired, key) {
                None => (),
                Some(_) => panic!("Replacing an entity in the entity_position map"),
            }
            mercenary.position = desired;
        }
    }

    fn remove_mercenary(&mut self, key: EntityKey) -> () {
        match (
            self.player_state_blue.mercenaries.remove(&key),
            self.player_state_red.mercenaries.remove(&key),
        ) {
            (None, None) => eprintln!(
                "Tried to remove mercenary with uid {}, but it does not exist",
                key.uid
            ),
            (Some(b), Some(r)) => {
                eprintln!("Mercenary with uid {} belongs to both teams", key.uid);
                match b.position == r.position {
                    true => match self.entity_position.remove(&r.position) {
                        Some(_) => (), // If you're really paranoid you can check this result and panic!
                        None => eprintln!(
                            "Mercenary with uid {} exists, but is not in the entity_position map",
                            key.uid
                        ),
                    },
                    false => panic!(
                        "Mercenary with uid {} is desynced between both teams!",
                        key.uid
                    ),
                }
            }
            (Some(b), None) => match self.entity_position.remove(&b.position) {
                Some(_) => (), // If you're really paranoid you can check this result and panic!
                None => eprintln!(
                    "Mercenary with uid {} exists, but is not in the entity_position map",
                    key.uid
                ),
            },
            (None, Some(r)) => match self.entity_position.remove(&r.position) {
                Some(_) => (), // If you're really paranoid you can check this result and panic!
                None => eprintln!(
                    "Mercenary with uid {} exists, but is not in the entity_position map",
                    key.uid
                ),
            },
        }
    }

    fn add_enemy(&mut self, position: Position, target_team: TeamColor) -> () {
        let target_player_state = match target_team {
            TeamColor::Red => &mut self.player_state_red,
            TeamColor::Blue => &mut self.player_state_blue,
        };
        match &target_player_state.base {
            Some(base) => match compute_path_to_enemy(position, &self.floor_tiles, base.position) {
                Ok(path_to_enemy) => {
                    let enemy = Enemy::new(position, target_team, path_to_enemy);
                    let key = EntityKey {
                        uid: enemy.uid,
                        entity_type: EntityType::Enemy,
                    };
                    match self.entity_position.insert(enemy.position, key) {
                        None => (),
                        Some(_) => panic!(
                            "Replacing an entity at position ({},{}), this line should not be reached",
                            enemy.position.x, enemy.position.y
                        ),
                    }
                    match self.enemies.insert(key, enemy) {
                        Some(_) => panic!(
                            "Replacing a enemy with uid {}, this line should not be reached",
                            key.uid
                        ),
                        None => (),
                    }
                }
                Err(e_str) => panic!(
                    "Enemy couldn't compute path to player base. Reason: {}",
                    e_str
                ),
            },
            None => panic!(
                "Enemy couldn't compute path to player base, because the the base does not exist"
            ),
        }
    }

    fn move_enemy(&mut self, enemy: &mut Enemy) -> () {
        match enemy.path_to_target.pop_front() {
            Some(new_pos) => {
                let old_pos = enemy.position;
                enemy.position = new_pos;
                let key = EntityKey {
                    uid: enemy.uid,
                    entity_type: EntityType::Mercenary,
                };
                match self.entity_position.remove(&old_pos) {
                    Some(_) => (), // could verify here and eprintln! due to desync
                    None => panic!("entity_position map is desynced"),
                }
                match self.entity_position.insert(new_pos, key) {
                    None => (),
                    Some(_) => panic!("Replacing an entity in the entity_position map"),
                }
            }
            None => eprintln!(
                "Attempted to move enemy despite its path being empty. This line should never be reached."
            ),
        }
    }

    fn remove_enemy(&mut self, key: EntityKey) -> () {
        match self.enemies.remove(&key) {
            Some(enemy) => match self.entity_position.remove(&enemy.position) {
                Some(_) => (),
                None => {
                    panic!(
                        "Removed enemy, but enemy wasn't in the entity position map as expected. Desync!"
                    )
                }
            },
            None => panic!("Tried to remove enemy, but enemy doesn't exist"),
        }
    }
}

////////// PLAYER ACTIONS + VALIDATION //////////
// TODO: use JSON schema to validate inputs more easily

fn try_set_team_name(
    game_state: &mut GameState,
    team_color: TeamColor,
    team_name: String,
) -> Result<(), String> {
    todo!()
}

// Buys a builder if possible. Returns an error if unable to buy a builder.
fn try_buy_builder(
    // we need to modify the game state if the input is valid
    game_state: &mut GameState,

    // we need to know which team this action is for
    team_color: TeamColor,
) -> Result<(), String> {

    // get the player state object for the team which is performing the bulider action
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };

    // see if there's a price listed for the next builder to buy
    match BUILDER_PRICES.get(player_state.builder_count as usize) {

        // Yes, there is a price for the next builder. Does the player have enough money?
        Some(&price) => match player_state.money >= price {

            // Player has enough money. Buy the builder.
            true => Ok({
                player_state.builder_count += 1;
                player_state.money -= price;
            }),

            // Player doesn't have enough money
            false => Err(format!(
                "The next builder costs ${}. You only have ${}",
                price, player_state.money
            )),
        },

        // No, there is not a price for the next builder: reached max amount of builders
        None => Err(format!(
            "The maximum number of builders per player is {}. You can't buy another one.",
            BUILDER_PRICES.len()
        )),
    }
}

// struct which gets deserialized from the agent, which represents a builder's action
#[derive(Deserialize)]
struct BuilderAction {
    // "build", "recycle_tower", "nothing"
    action_type: String,

    // mandatory
    target_x: Option<i32>,

    // mandatory
    target_y: Option<i32>,

    // Which type of tower: "crossbow", "minigun", etc.
    // see Tower::new() for how this will be parsed
    tower_type: Option<String>,
}

// Try to perform a builder action based on what the agent's output,
// Return an error if it was invalid, otherwise perform the action
fn try_perform_builder_action(

    // we need to modify the game state if the input is valid
    game_state: &mut GameState,

    // we need the input itself
    builder_action: BuilderAction,

    // we need to know which team this action is for
    team_color: TeamColor,
) -> Result<(), String> {
    // get the player state object for the team which is performing the bulider action
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };

    // which action are we doing?
    match builder_action.action_type.as_str() {

        // Building a tower
        "build" => match (builder_action.target_x, builder_action.target_y) {
            // if we put the target x and y positions into a tuple like (x,y), we have 4 options:

            // both target positions provided: is there a floor tile at the target position?
            (Some(x), Some(y)) => match game_state.floor_tiles.get(&Position { x, y }) {

                // Yes, there is a floor tile: do the team color and floor tile type match
                Some(tile) => match (tile, team_color) {

                    // Yes, the team color and floor tile type match
                    (FloorTile::RedTerritory, TeamColor::Red)
                    | (FloorTile::BlueTerritory, TeamColor::Blue) =>

                    // Is there already an entity at that position?
                    {
                        match game_state.entity_position.get(&Position { x, y }) {

                            // No entity already at the target position: did the agent specify a tower type to build?
                            None => match builder_action.tower_type {

                                // Yes, the agent specified a tower type.
                                Some(tow_type) => {

                                    // Attempt to create a tower with the specified tower type
                                    match Tower::new(
                                        Position { x, y },
                                        team_color,
                                        tow_type.clone(),
                                    ) {

                                        // Tower was successfully created (but not placed on the map yet)
                                        Ok(new_tower) => {

                                            // Does the player have enough money to place that tower?
                                            match player_state.money >= new_tower.stats.cost {

                                                // Yes, there is enough money to place the tower
                                                true => Ok({

                                                    // Complete the purchase and place the new tower
                                                    player_state.money -= new_tower.stats.cost;
                                                    game_state.add_tower(
                                                        tow_type,
                                                        Position { x, y },
                                                        team_color,
                                                    );
                                                }),

                                                // Not enough money to place the tower
                                                false => Err(format!(
                                                    "You're too poor to build the \"{}\" tower, which costs ${}. You only have ${}",
                                                    new_tower.stats.tower_type,
                                                    new_tower.stats.cost,
                                                    player_state.money
                                                )),
                                            }
                                        }

                                        // An error occurred when trying to create the tower
                                        Err(e_str) => Err(e_str),
                                    }
                                }

                                // No tower type was specified
                                None => Err(format!(
                                    "Builder action_type was \"build\", but no tower type was specified"
                                )),
                            },

                            // There is an entity in the way at the target position
                            Some(_) => Err(format!(
                                "There was already something at the target position ({},{})",
                                x, y
                            )),
                        }
                    }

                    // No, the team color and tile type don't match
                    _ => Err(format!(
                        "Builder attempted to build outside its team's territory"
                    )),
                },

                // there is no floor tile at the target position (out of bounds):
                None => Err(format!(
                    "Builder attempted to build somewhere out-of-bounds"
                )),
            },

            // no target positions provided
            (None, None) => Err(format!(
                "Builder action_type was \"build\", but no target position was specified"
            )),

            // only y position provided
            (None, Some(_)) => Err(format!(
                "Builder action_type was \"build\", but no target x position was specified"
            )),

            // only x position provided
            (Some(_), None) => Err(format!(
                "Builder action_type was \"build\", but no target y position was specified"
            )),
        },

        // Destroying the tower, recieve some money in return
        "recycle_tower" => match (builder_action.target_x, builder_action.target_y) {
            // if we put the target x and y positions into a tuple like (x,y), we have 4 options:

            // both target positions provided: is there a floor tile at the target position?
            (Some(x), Some(y)) => match game_state.floor_tiles.get(&Position { x, y }) {

                // Yes, there is a floor tile: do the team color and floor tile type match?
                Some(tile) => match (tile, team_color) {

                    // Yes, the team color and floor tile type match
                    (FloorTile::RedTerritory, TeamColor::Red)
                    | (FloorTile::BlueTerritory, TeamColor::Blue) => {

                        // Is there an entity at the target position?
                        match game_state.entity_position.get(&Position { x, y }).copied() {

                            // There's an entity at the target position. Is it a tower?
                            Some(entity_key) => match entity_key.entity_type {

                                // It's an EntityKey pointing to a tower. Is the key valid?
                                EntityType::Tower => match player_state.towers.get(&entity_key) {

                                    // It's pointing to a valid tower: Recycle the tower, and give back half it's cost
                                    Some(tower) => Ok({
                                        player_state.money += tower.stats.cost / 2;
                                        game_state.remove_tower(entity_key);
                                    }),

                                    // Invalid key: There's a desync between the entity and the tower
                                    None => Err(format!(
                                        "Dangling reference to tower with UID {} in entity lookup",
                                        entity_key.uid
                                    )),
                                },

                                // The entity is not a tower, can't recycle it
                                _ => Err(format!(
                                    "There is no tower to recycle at position ({},{})",
                                    x, y
                                )),
                            },

                            // There is nothing there to recycle
                            None => Err(format!(
                                "There is nothing to recycle at position ({},{})",
                                x, y
                            )),
                        }
                    }

                    // No, the team color and tile type don't match
                    _ => Err(format!(
                        "Builder attempted to recycle a tower outside its team's territory"
                    )),
                },

                // there is no floor tile at the target position (out of bounds):
                None => Err(format!(
                    "Builder attempted to recycle a tower somewhere out-of-bounds"
                )),
            },

            // no target position was provided
            (None, None) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target position was specified"
            )),

            // only y position provided
            (None, Some(_)) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target x position was specified"
            )),

            // only x position provided
            (Some(_), None) => Err(format!(
                "Builder action_type was \"recycle_tower\", but no target y position was specified"
            )),
        },

        // Builder chooses not to do anything
        "nothing" => Ok(()),
        invalid => Err(format!("Builder action_type \"{invalid}\" is invalid",)),
    }
}

// Queue a mercenary if it's possible to do so. Otherwise, return an error string.
fn try_queue_mercenary(
    // We need to modify the game state if the move is valid
    game_state: &mut GameState,

    // Which direction should the mercenary go?
    oct_direction: String,

    // Which team is queuing the mercenary?
    team_color: TeamColor,
) -> Result<(), String> {
    // Get the player state object for the team which is performing the bulider action
    let player_state = match team_color {
        TeamColor::Red => &mut game_state.player_state_red,
        TeamColor::Blue => &mut game_state.player_state_blue,
    };

    // Get the specified player's base
    match &mut player_state.base {

        // Player's base exists. Get the position where the new mercenary would go.
        Some(player_base) => match parse_direction(oct_direction, player_base.position) {

            // Able to get the new mercenary's position. Is there a floor tile at that position?
            Ok(new_pos) => match game_state.floor_tiles.get(&new_pos) {

                // There's a floor tile at the new mercenary's position. What kind of tile is it?
                Some(floor_tile) => match floor_tile {

                    // There's a path tile at the new mercenary's position.
                    // Does the player have enough money to buy the new mercenary?
                    FloorTile::Path => match player_state.money >= MERCENARY_PRICE {

                        // Player has enough money to buy the new mercenary. Buy the mercenary and queue it.
                        true => Ok({
                            player_state.money -= MERCENARY_PRICE;
                            player_base.mercenaries_queued.push_back(new_pos);
                        }),

                        // Player does not have enough money. Error
                        false => Err(format!(
                            "You're too poor to buy a mercenary. Mercenaries cost ${}. You only have ${}.",
                            MERCENARY_PRICE, player_state.money
                        )),
                    },
                    _ => Err(format!("Mercenary must start on a path tile")),
                },

                // There's no floor tile at the new mercenary's position. Error
                None => Err(format!("Mercenary can't go out-of-bounds")),
            },

            // Unable to get new mercenary's position. Error
            Err(e_str) => Err(e_str),
        },

        // Player's base does not exist. Error
        None => Err(format!(
            "Player base does not exist, cannot queue mercenary"
        )),
    }
}

////////// WORLD UPDATE //////////

fn move_mercenaries(game_state: &mut GameState) -> () {
    let mut conflicts: HashMap<Position, Vec<&Mercenary>> = HashMap::new();
    for merc in game_state.player_state_red.mercenaries.values() {
        let desire = &merc.get_desired_position();
        match conflicts.get_mut(desire) {
            Some(other) => other.push(merc),
            None => {
                let mut new = Vec::new();
                new.push(merc);
                conflicts.insert(merc.position, new);
            }
        }
    }
    for merc in game_state.player_state_blue.mercenaries.values() {
        let desire = &merc.get_desired_position();
        match conflicts.get_mut(desire) {
            Some(other) => other.push(merc),
            None => {
                let mut new = Vec::new();
                new.push(merc);
                conflicts.insert(merc.position, new);
            }
        }
    }
    for conflict in conflicts {}
}

fn pop_mercenaries(game_state: &mut GameState) -> () {
    match &mut game_state.player_state_blue.base {
        Some(base) => match base.mercenaries_queued.pop_front() {
            Some(new_pos) => {
                game_state.add_mercenary(TeamColor::Blue, new_pos);
            }
            None => (),
        },
        None => panic!("Blue player base is uninitialized while spawning new mercenaries"),
    }

    match &mut game_state.player_state_blue.base {
        Some(base) => match base.mercenaries_queued.pop_front() {
            Some(new_pos) => {
                game_state.add_mercenary(TeamColor::Red, new_pos);
            }
            None => (),
        },
        None => panic!("Red player base is uninitialized while spawning new mercenaries"),
    }
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
