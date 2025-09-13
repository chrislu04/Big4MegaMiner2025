extends Node2D


const ALT_GRASS = preload("res://Assets/Base_Skin/alt_grass.png")
const ALT_PATH = preload("res://Assets/Base_Skin/alt_path.png")
const GRASS = preload("res://Assets/Base_Skin/grass.png")
const PATH = preload("res://Assets/Base_Skin/path.png")

var placeholder : bool = false

var player1_ai : bool
var player2_ai : bool

var alt : bool = false
@onready var tiles = $Tiles

## Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	player1_ai = is_ai1
	player2_ai = is_ai2
	
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, GlobalPaths.AI_agent1_file_path, GlobalPaths.AI_agent2_file_path], output)
	print(output)
	for i in output:
		print(i)
	## Draw the map, bases, & enemy spawners
	
	## Set team names
	
	## Draw the finished start
	_draw_game_from_gamestate("place_holder")
	

## Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	## We're currently using a dummy game_state for testing purposes
	var jsonfile = FileAccess.open("res://Data/dummy.json", FileAccess.READ)
	var game_state_json = JSON.parse_string(jsonfile.get_as_text())
	
	
	
	_draw_grid(game_state_json)
	
	#_draw_entities(game_state_json)

func _draw_grid(game_state_json : Dictionary):
	var previous_y = 0
	var highest_x : float
	var highest_y : float
	
	for tile : String in game_state_json["floor_tiles"]:
		
		var tile_info = JSON.parse_string(tile)
		if tile_info["x"] > highest_x:
			highest_x = tile_info["x"]
		if tile_info["y"] > highest_y:
			highest_y = tile_info["y"]
		
		
		if tile_info["y"] == previous_y:
			alt = !alt
		else:
			previous_y = tile_info["y"]
		
		if (game_state_json["floor_tiles"][tile] == 2):
			var sprite = Sprite2D.new()
			if alt:
				sprite.texture = ALT_PATH
			else:
				sprite.texture = PATH
			
			sprite.position = Vector2(tile_info["x"] * 32, tile_info["y"] * 32)
			tiles.add_child(sprite)
		else:
			var sprite = Sprite2D.new()
			if alt:
				sprite.texture = ALT_GRASS
			else:
				sprite.texture = GRASS
			
			sprite.position = Vector2(tile_info["x"] * 32, tile_info["y"] * 32)
			tiles.add_child(sprite)
	
	tiles.position.x = (get_viewport_rect().size.x - (highest_x * 32)) / 2
	tiles.position.y = (get_viewport_rect().size.y - (highest_y * 32)) / 2

## Draws the mercanaries, enemies, spawner, buildings
func _draw_entities(game_state_json : Dictionary):
	
	for entity : String in game_state_json["entity_position"]:
		var entity_info = JSON.parse_string(entity)
		print(entity_info)
		if game_state_json["entity_position"][entity]["entity_type"] == "mercenary": ## <-- Error at this line, fix it later
			var sprite = Sprite2D.new()
			sprite.texture = preload("res://Assets/Base_Skin/blue_recruit.png")
			sprite.position = Vector2(game_state_json["entity_position"]["x"],game_state_json["entity_position"]["y"])
			
	

## Make this when the game backend is done
func _process(delta):
	
	if placeholder:
		## First Grab current gamestate from backend, save it to output
		#var output = []
		#OS.execute("python.exe", ["MegaMiner_BackEnd/main.py",10, "Hi"], output)
		#
		### Second, execute the python files with the gamestate as a parametter, then save the output actions
		#var agentOutput1 = []
		#var agentOutput2 = []
		#OS.execute("python.exe", [GlobalPaths.AI_agent1_file_path], agentOutput1)
		#OS.execute("python.exe", [GlobalPaths.AI_agent2_file_path], agentOutput2)
		
		## Send the output actions to the backend, save the new gamestate
		#OS.execute("whatever.exe", ["function_arguments"], output) ##The backend isn't finished
		
		## draw the new gamestate
		_draw_game_from_gamestate("place_holder")
		
		pass


func _on_ui_build(red_side: bool, x: int, y: int) -> void:
	var output = []
	OS.execute("python", [GlobalPaths.backendPath, x, y, output])
