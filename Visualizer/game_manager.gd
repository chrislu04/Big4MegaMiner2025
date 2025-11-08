extends Node2D


const GRASS_RED_TEX = preload("res://Assets/HD_Skin/grass_red.png")
const GRASS_BLUE_TEX = preload("res://Assets/HD_Skin/grass_blue.png")
const PATH_TEX = preload("res://Assets/HD_Skin/path.png")
const BLUE_RECRUIT = preload("res://Assets/Topdown skin/blue recruit.png")

const RED_RECRUIT = preload("uid://can1bceehb1qy")

const ENEMY = preload("res://Assets/Topdown skin/enemy.png")

const BASE = preload("res://Assets/Topdown skin/base.png")
const CROSSBOW = preload("res://Assets/Topdown skin/crossbow.png")
const CANNON = preload("uid://px2v73fj7qag")
const GATLING = preload("uid://2cfukvxbe1ah")
const HOUSE = preload("uid://bciq54f3p3yiw")

const RED_CASTLE : Texture = preload("res://Assets/HD_Skin/base.svg")

@export var UI : GameUI

var previous_game_state : Dictionary 
var current_game_state : Dictionary

var is_player1_ai : bool
var is_player2_ai : bool

var play1ready : bool = false
var play2ready : bool = false

var initial : bool  = true

var backend_running : bool = false

var turn_interval_max : float = 2.0 
var turn_interval : float = 0
var path_to_game_state

@onready var world: Node2D = $World
@onready var tiles = $World/Tiles
@onready var mercenaries: Node2D = $World/Mercenaries
@onready var towers: Node2D = $World/Towers
@onready var demons: Node2D = $World/Demons
@onready var misc_entities: Node2D = $"World/Misc Entities"

var processID
var stdio : FileAccess
var thread
var stderr : FileAccess


func _ready():
	UI.action.connect(_on_ui_action)
	

# Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	is_player1_ai = is_ai1
	is_player2_ai = is_ai2
	var process_info 
	
	if is_ai1 and is_ai2:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.default_map, "-a1", GlobalPaths.AI_agent1_file_path, "-a2",GlobalPaths.AI_agent2_file_path, "-v"], 
			true)
		
	elif not is_ai1 and is_ai2:
		
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.default_map, "-h1" , "-a2",GlobalPaths.AI_agent2_file_path, "-v"], 
			true)
		play2ready = true
	elif is_ai1 and not is_ai2:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.default_map, "-a1", GlobalPaths.AI_agent1_file_path, "-h2", "-v"], 
			true)
		play1ready = true
	else:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.default_map, "-h1", "-h2", "-v"], 
			true)
	
	
	
	processID = process_info["pid"]
	stdio = process_info["stdio"]
	stderr = process_info["stderr"]
	
	if stdio != null:
		print(stdio.get_line())
		var content = stdio.get_line() ##Initial State
		print(stdio.get_line())
		print(stdio.get_line())
		print(stdio.get_line())
		var first_turn
		if is_ai1 and is_ai2:
			first_turn = stdio.get_line() #First turn
	
	
		_draw_game_from_gamestate(content)
		if is_ai1 and is_ai2:
			await get_tree().create_timer(2.0).timeout
			_draw_game_from_gamestate(first_turn)
			turn_interval = turn_interval_max
		backend_running = true


# Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	var game_state_json = JSON.parse_string(game_state)
	current_game_state = game_state_json
	
	if initial:
		_draw_grid(game_state_json["FloorTiles"])
		
		## Setting up castles
		var castle = Sprite2D.new()
		
		castle.texture = RED_CASTLE
		castle.scale.x = 32 /  RED_CASTLE.get_size().x
		castle.scale.y = 32 / RED_CASTLE.get_size().y
		
		castle.position = Vector2(game_state_json["PlayerBaseR"]["x"] * 32, game_state_json["PlayerBaseR"]["y"] * 32)
		misc_entities.add_child(castle)
		
		var castle_b = Sprite2D.new()
		
		castle_b.texture = preload("uid://bh23hjmsxnw56")
		castle_b.scale.x = 32 /  castle_b.texture.get_size().x
		castle_b.scale.y = 32 / castle_b.texture.get_size().y
		
		castle_b.position = Vector2(game_state_json["PlayerBaseB"]["x"] * 32, game_state_json["PlayerBaseB"]["y"] * 32)
		misc_entities.add_child(castle_b)
		
		
		initial = false
	
	
	_draw_mercenaries(game_state_json["Mercenaries"])
	_draw_towers(game_state_json["Towers"])
	_draw_demons(game_state_json["Demons"])
	_update_ui(game_state_json)


func _draw_grid(tile_grid : Array):
	var layer_y : int = 0
	var alt_y = false
	for layer in tile_grid:
		var character_x = 0
		var alt_x = false
		
		for character in layer:
			var sprite = Sprite2D.new()

			if character == 'b':
				sprite.texture = GRASS_BLUE_TEX
			elif character == 'O':
				sprite.texture = PATH_TEX
			elif character == 'r':
				sprite.texture = GRASS_RED_TEX
			
			if alt_x == alt_y:
				sprite.self_modulate = Color8(255, 255, 255)
			else:
				sprite.self_modulate = Color8(200, 200, 200)
			
			sprite.scale = Vector2(0.125,0.125)
			sprite.position = Vector2(character_x * 32, layer_y * 32)
			tiles.add_child(sprite)
			character_x += 1
			
			alt_x = !alt_x
			
		layer_y += 1
		alt_y = !alt_y
	
	
	
	world.position.x = (get_viewport_rect().size.x - (tile_grid[0].length() * 32)) / 2
	world.position.y = (get_viewport_rect().size.y - (tile_grid.size() * 32)) / 2
	GlobalPaths.tile_grid = tiles

#func _delete_mercs():
	#for i in mercenaries.get_children():
		#i.queue_free()

# Draws the mercanaries
func _draw_mercenaries(mercs : Array):
	#print(mercs)
	var count = 0
	for merc in mercs:
		if mercenaries.get_child_count() - 1 < count:
			var pos = Vector2(merc["x"] * 32, merc["y"] * 32)
			var sprite = Sprite2D.new()
			if merc["Team"] == "b":
				sprite.texture = BLUE_RECRUIT
				sprite.flip_h = true
			else:
				sprite = RED_RECRUIT.instantiate()
			
			sprite.position = pos
			mercenaries.add_child(sprite)
		else:
			var child = mercenaries.get_child(count)
			var tween = get_tree().create_tween()
			if merc["State"] == "dead":
				child.queue_free()
				count -= 1
			elif merc["State"] == "moving":
				if merc["Team"] == "r":
					child.move(position - Vector2(merc["x"] * 32, merc["y"] * 32))
				tween.tween_property(child, "position", Vector2(merc["x"] * 32, merc["y"] * 32), turn_interval_max)
			else:
				if merc["Team"] == "r":
					child.attack(Vector2(1,0))
		
		count += 1

func _draw_towers(data_towers : Array):
	print(data_towers)
	for tower in data_towers:
		var base = Sprite2D.new()
		var current_tower = Sprite2D.new()
		var pos = Vector2(tower["x"] * 32, tower["y"] * 32)
		base.position = pos
		base.texture = BASE
		towers.add_child(base)
		
		#var type_c = tower["Type"]
		match tower["Type"]:
			"Crossbow":
				current_tower.texture = CROSSBOW
			"Cannon":
				current_tower.texture = CANNON
			"Minigun":
				current_tower.texture = GATLING
			"House":
				current_tower.texture = HOUSE
		
		current_tower.scale = Vector2(32 / current_tower.texture.get_size().x, 32 / current_tower.texture.get_size().y)
		base.add_child(current_tower)
		current_tower.rotation_degrees = tower["AimAngle"]

func _draw_demons(dem_array : Array):
	var count = 0
	for dem in dem_array:
		if demons.get_child_count() - 1 < count:
			var pos = Vector2(dem["x"] * 32, dem["y"] * 32)
			var sprite = Sprite2D.new()
			if dem["Team"] == "b":
				sprite.flip_h = true
				
			sprite.texture = ENEMY
			
			sprite.position = pos
			demons.add_child(sprite)
		else:
			var child : Sprite2D = demons.get_child(count)
			var tween = get_tree().create_tween()
			if dem["State"] == "dead":
				child.queue_free()
				count -= 1
			else:
				tween.tween_property(child, "position", Vector2(dem["x"] * 32, dem["y"] * 32), turn_interval_max)
		count += 1

# Make this when the game backend is done
func _process(delta):
	
	if backend_running:
		if is_player1_ai and is_player2_ai: ## If both players are AI
			turn_interval -= 1.0 * delta
			if turn_interval <= 0:
				AI_game_turn()
				turn_interval = turn_interval_max
		else:
			if play1ready and play2ready:
				
				if stdio.get_error() == OK:
					var content = stdio.get_line()
					
					if !content.begins_with("--WINNER"):
						previous_game_state = current_game_state
						_draw_game_from_gamestate(content)
					else:
						print(content)
						backend_running = false
					stdio.store_line("--NEXT TURN--")
					stdio.flush() # Ensure data is written to the pipe
				
				play1ready = is_player1_ai
				play2ready = is_player2_ai

func AI_game_turn():
	var content : String = ""
	if stdio.get_error() == OK:
		stdio.store_line("--NEXT TURN--")
		stdio.flush() # Ensure data is written to the pipe
		content = stdio.get_line()
	else:
		printerr("Open file error: ", stdio.get_error())
		backend_running = false
	
	previous_game_state = current_game_state
	
	if !content.begins_with("--WINNER"):
		_draw_game_from_gamestate(content)
	else:
		backend_running = false


func _on_ui_action(is_player1 : bool, action : String , x: int, y: int, to_build : String ,merc : String) -> void:
	if is_player1:
		play1ready = true
	else:
		play2ready = true
	
	if stdio.get_error() == OK:
		var player_action = "{\"action\": \"" + action + "\", \"x\": " + str(x) + ", \"y\": " + str(y) + ", \"tower_type\": \"" + to_build + "\", \"merc_direction\": \"" + merc + "\"}"
		#print(player_action)
		stdio.store_line(player_action)
		stdio.flush() # Ensure data is written to the pipe

func _update_ui(gamestate):
	UI._update_turns_progressed(gamestate["TurnsRemaining"])

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if processID != null:
			OS.kill(processID) ##Terminates the process
			get_tree().quit()

func _close_backend():
	stdio.close()
	stderr.close()
	OS.kill(processID)
