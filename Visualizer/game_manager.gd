extends Node2D


const ALT_GRASS = preload("res://Assets/Base_Skin/alt_grass.png")
const ALT_PATH = preload("res://Assets/Base_Skin/alt_path.png")
const GRASS = preload("res://Assets/Base_Skin/grass.png")
const PATH = preload("res://Assets/Base_Skin/path.png")


const BLUE_RECRUIT = preload("res://Assets/Topdown skin/blue recruit.png")
const RED_RECRUIT = preload("res://Assets/Topdown skin/red recruit.png")
const ENEMY = preload("res://Assets/Topdown skin/enemy.png")
const BASE = preload("res://Assets/Topdown skin/base.png")
const CROSSBOW = preload("res://Assets/Topdown skin/crossbow.png")

@export var UI : GameUI

var previous_game_state : Dictionary 
var current_game_state : Dictionary

var player1_ai : bool
var player2_ai : bool

var alt : bool = false
var initial : bool  = true
var backend_running : bool = false

var turn_interva_max : float = 2.0 
var turn_interval : float = 0
var path_to_game_state

@onready var tiles = $Tiles
@onready var mercenaries: Node2D = $Mercenaries
@onready var towers: Node2D = $Towers
@onready var demons: Node2D = $Demons
@onready var misc_entities: Node2D = $"Misc Entities"


# Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	player1_ai = is_ai1
	player2_ai = is_ai2
	
	var output = []
	var exit_code = OS.execute( 				\
		"python", 								\
		[ 										\
			GlobalPaths.backendPath, 			\
			"-v", "-i", 						\
			GlobalPaths.AI_agent1_file_path, 	\
			GlobalPaths.AI_agent2_file_path 	\
		], 										\
		output, true 							\
	)
	
	if exit_code == 0:
		pass
		print("Python Script executted successfully!")
	else:
		print("Error handling script!: ", exit_code)
	
	var content
	var path_to_game_state : String = GameSettings.convert_string_to_readable(output[0]).strip_edges(false, true)
	
	if FileAccess.file_exists(path_to_game_state):
		var file = FileAccess.open(path_to_game_state, FileAccess.READ)
		if file:
			content = file.get_as_text()
			file.close()
		else:
			printerr("Couldn't Open File! ", FileAccess.get_open_error())
	else:
		printerr("File doesn't exist!")

	_draw_game_from_gamestate(content)
	backend_running = true


# Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	var game_state_json = JSON.parse_string(game_state)
	current_game_state = game_state_json
	print(current_game_state)
	if initial:
		_draw_grid(game_state_json["TileGrid"])
		initial = false
	#_delete_mercs()
	
	_draw_mercenaries(game_state_json["Mercenaries"])
	_draw_towers(game_state_json["Towers"])
	_draw_demons(game_state_json["Demons"])
	_update_ui(game_state_json)


func _draw_grid(tile_grid : Array):
	var previous_y = 0
	
	for x in range(tile_grid.size()):
		for y in range(tile_grid[x].size()):
			alt = !alt
			if previous_y == y:
				alt = !alt
			else:
				previous_y = y
			
			var sprite = Sprite2D.new()
			if tile_grid[x][y] == 'b':
				if alt:
					sprite.texture = ALT_GRASS
				else:
					sprite.texture = GRASS
			elif tile_grid[x][y] == 'r':
				if alt:
					sprite.texture = ALT_GRASS
				else:
					sprite.texture = GRASS
			elif tile_grid[x][y] == 'Path':
				if alt:
					sprite.texture = ALT_PATH
				else:
					sprite.texture = PATH
			
			sprite.position = Vector2(x * 32, y * 32)
			tiles.add_child(sprite)
	
	tiles.position.x = (get_viewport_rect().size.x - (tile_grid.size() * 32)) / 2
	tiles.position.y = (get_viewport_rect().size.y - (tile_grid[0].size() * 32)) / 2
	mercenaries.position = tiles.position
	towers.position = tiles.position
	demons.position = tiles.position
	misc_entities.position = tiles.position

#func _delete_mercs():
	#for i in mercenaries.get_children():
		#i.queue_free()

# Draws the mercanaries
func _draw_mercenaries(mercs : Array):
	print(mercs)
	var count = 0
	for merc in mercs:
		if mercenaries.get_child_count() - 1 < count:
			var pos = Vector2(merc["Mercenary"]["x"] * 32, merc["Mercenary"]["y"] * 32)
			var sprite = Sprite2D.new()
			if merc["Mercenary"]["Team"] == "b":
				sprite.texture = BLUE_RECRUIT
				sprite.flip_h = true
			else:
				sprite.texture = RED_RECRUIT
			
			sprite.position = pos
			mercenaries.add_child(sprite)
		else:
			var child : Sprite2D = mercenaries.get_child(count)
			var tween = get_tree().create_tween()
			if merc["Mercenary"]["state"] == "dead":
				child.queue_free()
				count -= 1
			else:
				tween.tween_property(child, "position", Vector2(merc["Mercenary"]["x"] * 32, merc["Mercenary"]["y"] * 32), 1.0)
		
		count += 1

func _draw_towers(data_towers : Array):
	
	for tower in data_towers:
		var base = Sprite2D.new()
		var type = Sprite2D.new()
		var pos = Vector2(tower["x"] * 32, tower["y"] * 32)
		base.position = pos
		base.texture = BASE
		towers.add_child(base)
		
		var type_c = tower["Type"]
		match tower["Type"]:
			"Crossbow":
				type.texture = CROSSBOW
		base.add_child(type)
		type.rotation_degrees = tower["AimAngle"]

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
			if dem["state"] == "dead":
				child.queue_free()
				count -= 1
			else:
				tween.tween_property(child, "position", Vector2(dem["x"] * 32, dem["y"] * 32), 1.0)
		count += 1

# Make this when the game backend is done
func _process(delta):
	
	if backend_running:
		turn_interval -= 1.0 * delta
		if turn_interval <= 0:
			AI_game_turn()
			turn_interval = turn_interva_max
		

func AI_game_turn():
	var output = []
	var exit_code = OS.execute("python", [GlobalPaths.backendPath, "-v", GlobalPaths.AI_agent1_file_path, GlobalPaths.AI_agent2_file_path], output, true)
	if exit_code == 0:
		pass
		#print("Python Script executted successfully!")
	else:
		print("Error handling script!: ", exit_code)
	
	previous_game_state = current_game_state
	
	var content
	var path_to_game_state : String = GameSettings.convert_string_to_readable(output[0]).strip_edges(false, true)
	
	if FileAccess.file_exists(path_to_game_state):
		var file = FileAccess.open(path_to_game_state, FileAccess.READ)
		if file:
			content = file.get_as_text()
			file.close()
		else:
			printerr("Couldn't Open File! ", FileAccess.get_open_error())
	else:
		printerr("File doesn't exist!")
	
	#print(output[0])
	_draw_game_from_gamestate(content)


func _on_ui_build(red_side: bool, x: int, y: int) -> void:
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, x, y, output])


func _update_ui(gamestate):
	UI._update_turns_progressed(gamestate["TurnsProgressed"])
	UI._update_money_values(gamestate["RedPlayer"]["Money"], gamestate["BluePlayer"]["Money"])
	UI._update_base_health(true,gamestate["RedPlayer"]["Health"])
	UI._update_base_health(false,gamestate["BluePlayer"]["Health"])
