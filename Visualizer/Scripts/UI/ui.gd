class_name GameUI
extends CanvasLayer



@onready var main_menu : Control = $"Main Menu"

@onready var human_ai_select : Control = $"Human AI select"

@onready var game_ui: Control = $"Game UI"

var ai1 : bool = false
var ai2 : bool = false

signal start_game(is_ai1 : bool, is_ai2 : bool)

signal action(player_1 : bool, build : String, x : int, y : int, tower_to_build : String ,merc_direction : String)

var red_turn : bool = true

func _ready():
	main_menu.visible = true
	human_ai_select.visible = false
	game_ui.visible = false

func _process(_delta: float) -> void:
	pass

func _update_turns_progressed(new_value):
	$"Game UI/Turns/Turns Progressed".text = "Turns Left\n" + str(int(new_value))

func _update_money_values(left_value, right_value):
	$"Game UI/LeftSideStates/Money/Money".text = "$" + str(left_value)
	
	$"Game UI/RightSideStates/Money/Money".text = "$" + str(right_value)


func _update_base_health(is_left : bool, new_value):
	if is_left:
		$"Game UI/LeftSideStates/Health/Health".text = "Base Health\n" + str(new_value) + "/200"
	else:
		$"Game UI/RightSideStates/Health/Health".text = "Base Health\n" + str(new_value) + "/200"

func _on_main_menu_play_game() -> void:
	human_ai_select.visible = true
	main_menu.visible = false


func _on_human_ai_select_go(is_ai: bool, is_ai2: bool) -> void:
	ai1 = is_ai
	ai2 = is_ai2
	
	if ai1 and ai2:
		pass
	elif not ai1 and ai2:
		red_turn = true
	elif ai1 and not ai2:
		red_turn = false
	else:
		pass
	
	start_game.emit(is_ai, is_ai2)
	main_menu.hide()
	human_ai_select.hide()
	game_ui.show()
	if !is_ai:
		$"Game UI/LeftSideStates".active = true
		$"Game UI/LeftSideStates/Human Control".visible = true
	if !is_ai2:
		$"Game UI/RightSideStates".active = true
		$"Game UI/RightSideStates/Human Control".visible = true

func _on_human_ai_select_back() -> void:
	main_menu.visible = true
	human_ai_select.visible = false


func _on_right_side_states_action(is_player1: bool, build: String, x: int, y: int, tower_to_build: String, merc_direction: String) -> void:
	if is_player1 == red_turn:
		action.emit(is_player1, build, x, y, tower_to_build, merc_direction)
		if ai1 == ai2:
			red_turn = !red_turn
			
			$"Game UI/Turns/Player Turn".modulate = Color(255,255,255)
			if red_turn:
				$"Game UI/Turns/Player Turn".text = "Red Player's Turn\n<---"
				var tween = get_tree().create_tween()
				tween.tween_property($"Game UI/Turns/Player Turn", "modulate", Color(255,255,255,0), 5.0)
				$"Game UI/AnimationPlayer".play("red Side glow")
				print("Red players turn!")
			else:
				$"Game UI/Turns/Player Turn".text = "Blue Player's Turn\n--->"
				var tween = get_tree().create_tween()
				tween.tween_property($"Game UI/Turns/Player Turn", "modulate", Color(255,255,255,0), 5.0)
				$"Game UI/AnimationPlayer".play("blue side glow")
				print("blue players turn!")

func on_next_turn():
	$"Game UI/LeftSideStates"._on_next_turn()
	$"Game UI/RightSideStates"._on_next_turn()
	
