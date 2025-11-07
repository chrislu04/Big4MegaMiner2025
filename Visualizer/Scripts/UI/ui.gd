class_name GameUI
extends CanvasLayer



@onready var main_menu : Control = $"Main Menu"

@onready var human_ai_select : Control = $"Human AI select"

@onready var game_ui: Control = $"Game UI"

signal start_game(is_ai1 : bool, is_ai2 : bool)


signal action(player_1 : bool, build : String, x : int, y : int, tower_to_build : String ,merc_direction : String)


func _ready():
	main_menu.visible = true
	human_ai_select.visible = false
	game_ui.visible = false


func _on_build_pressed(build : String, x : int, y : int, merc_direction : String) -> void:
	action.emit(build, x, y , merc_direction)

func _update_turns_progressed(new_value):
	$"Game UI/Panel/Turns Progressed".text = "Turns Left\n" + str(int(new_value))


func _on_main_menu_play_game() -> void:
	human_ai_select.visible = true
	main_menu.visible = false


func _on_human_ai_select_go(is_ai: bool, is_ai2: bool) -> void:
	start_game.emit(is_ai, is_ai2)
	main_menu.hide()
	human_ai_select.hide()
	game_ui.show()
	if !is_ai:
		$"Game UI/RightSideStates/Human Control".active = true
		$"Game UI/RightSideStates/Human Control".visible = true
		



func _on_human_ai_select_back() -> void:
	main_menu.visible = true
	human_ai_select.visible = false


func _on_right_side_states_action(player1: bool, build: String, x: int, y: int, tower_to_build: String, merc_direction: String) -> void:
	action.emit(player1, build, x, y, tower_to_build, merc_direction)
