extends Node2D


const ALT_GRASS = preload("res://Assets/Base_Skin/alt_grass.png")
const ALT_PATH = preload("res://Assets/Base_Skin/alt_path.png")
const GRASS = preload("res://Assets/Base_Skin/grass.png")
const PATH = preload("res://Assets/Base_Skin/path.png")

var previous_game_state : String = ""
var current_game_state : String = ""

var player1_ai : bool
var player2_ai : bool

var alt : bool = false

var initial : bool  = true

@onready var tiles = $Tiles
@onready var entities: Node2D = $Entities

## Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	player1_ai = is_ai1
	player2_ai = is_ai2
	
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, "-v"], output)
	
	for i in output:
		print(i)
	#_draw_game_from_gamestate(output[0])
	

## Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	## We're currently using a dummy game_state for testing purposes
	var jsonfile = FileAccess.open("res://Data/intial.json", FileAccess.READ)
	var game_state_json = JSON.parse_string(game_state)
	
	if initial:
		_draw_grid(game_state_json["TileGrid"])
		
		initial = false
	
	#_draw_entities(game_state_json)

func _update_grid_grom_gamestate():
	pass

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

## Draws the mercanaries, enemies, spawner, buildings
func _draw_entities(game_state_json : Array):
	
	pass
	

## Make this when the game backend is done
func _process(delta):
	
	#if placeholder:
		### First Grab current gamestate from backend, save it to output
		##var output = []
		##OS.execute("python.exe", ["MegaMiner_BackEnd/main.py",10, "Hi"], output)
		##
		#### Second, execute the python files with the gamestate as a parametter, then save the output actions
		##var agentOutput1 = []
		##var agentOutput2 = []
		##OS.execute("python.exe", [GlobalPaths.AI_agent1_file_path], agentOutput1)
		##OS.execute("python.exe", [GlobalPaths.AI_agent2_file_path], agentOutput2)
		#
		### Send the output actions to the backend, save the new gamestate
		##OS.execute("whatever.exe", ["function_arguments"], output) ##The backend isn't finished
		#
		### draw the new gamestate
		#_draw_game_from_gamestate("place_holder")
		
		pass


func _on_ui_build(red_side: bool, x: int, y: int) -> void:
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, x, y, output])
