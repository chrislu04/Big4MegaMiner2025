extends Node2D


const ALT_GRASS = preload("res://Assets/Base_Skin/alt_grass.png")
const ALT_PATH = preload("res://Assets/Base_Skin/alt_path.png")
const GRASS = preload("res://Assets/Base_Skin/grass.png")
const PATH = preload("res://Assets/Base_Skin/path.png")
const BLUE_RECRUIT = preload("res://Assets/Base_Skin/blue_recruit.png")
const RED_RECRUIT = preload("res://Assets/Base_Skin/red_recruit.png")

const BASE = preload("res://Assets/Base_Skin/base.png")
const CROSSBOW = preload("res://Assets/Base_Skin/crossbow.png")

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

@onready var tiles = $Tiles
@onready var entities: Node2D = $Entities

## Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	player1_ai = is_ai1
	player2_ai = is_ai2
	
	var output = []
	var exit_code = OS.execute("python", [GlobalPaths.backendPath, "-v", "initial"], output, true)
	
	if exit_code == 0:
		print("Python Script executted successfully!")
	else:
		print("Error handling script!: ", exit_code)
	#for i in output:
		#print(i)
	
	_draw_game_from_gamestate(output[0])
	backend_running = true

## Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	var game_state_json = JSON.parse_string(game_state)
	current_game_state = game_state_json
	
	if initial:
		_draw_grid(game_state_json["TileGrid"])
		initial = false
	_delete_mercs()
	
	_draw_mercenaries(game_state_json["Mercenaries"])
	_draw_towers(game_state_json["Towers"])
	
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
	entities.position = tiles.position

func _delete_mercs():
	for i in entities.get_children():
		i.queue_free()

## Draws the mercanaries
func _draw_mercenaries(mercs : Array):
	
	for merc in mercs:
		var pos = Vector2(merc["Mercenary"]["x"] * 32, merc["Mercenary"]["y"] * 32)
		var sprite = Sprite2D.new()
		if merc["Mercenary"]["Team"] == "b":
			sprite.texture = BLUE_RECRUIT
			sprite.flip_h = true
		else:
			sprite.texture = RED_RECRUIT
		
		sprite.position = pos
		entities.add_child(sprite)

func _draw_towers(towers : Array):
	
	
	for tower in towers:
		var base = Sprite2D.new()
		var type = Sprite2D.new()
		var pos = Vector2(tower["x"] * 32, tower["y"] * 32)
		base.position = pos
		base.texture = BASE
		entities.add_child(base)
		
		var type_c = tower["Type"]
		match tower["Type"]:
			"Crossbow":
				type.texture = CROSSBOW
		base.add_child(type)
		type.rotation = tower["AimAngle"]

## Make this when the game backend is done
func _process(delta):
	
	if backend_running:
		turn_interval -= 1.0 * delta
		if turn_interval <= 0:
			AI_game_turn()
			turn_interval = turn_interva_max
		


func AI_game_turn():
	var output = []
	var exit_code = OS.execute("python", [GlobalPaths.backendPath, "-v"], output, true)
	if exit_code == 0:
		pass
		#print("Python Script executted successfully!")
	else:
		print("Error handling script!: ", exit_code)
	
	previous_game_state = current_game_state
	
	_draw_game_from_gamestate(output[0])

func _on_ui_build(red_side: bool, x: int, y: int) -> void:
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, x, y, output])

func _update_ui(gamestate):
	UI._update_turns_progressed(gamestate["TurnsProgressed"])
