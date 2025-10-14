class_name GameUI
extends CanvasLayer

@export var player_select_one : PlayerSelect
@export var player_select_two : PlayerSelect

@onready var main_menu : Control = $"Main Menu"

@onready var human_ai_select : Control = $"Human AI select"

@onready var game_ui: Control = $"Game UI"

signal start_game(is_ai1 : bool, is_ai2 : bool)

signal build(red_side : bool, x : int, y : int)
signal destroy(red_side : bool , x: int,y :  int)
signal queue_mercenary(red_side : bool, top : bool, bottom : bool)

func _ready():
	main_menu.visible = true
	human_ai_select.visible = false
	game_ui.visible = false

func _on_play_game_pressed():
	main_menu.visible = false
	human_ai_select.visible = true


func _on_watch_replay_pressed():
	pass # Replace with function body.


func _on_quit_pressed():
	get_tree().quit()


func _on_back_pressed():
	main_menu.visible = true
	human_ai_select.visible = false

func _on_go_pressed(): ## I love hard coding!
	var player1_ready : bool = player_select_one.line_edit.text != "" ##If the text is "" then you either havent picked a file or haven't selected a team name
	var player2_ready : bool = player_select_two.line_edit.text != ""
	
	game_ui.visible = true
	
	if player1_ready && player2_ready:
		start_game.emit(player_select_one.is_AI, player_select_two.is_AI)
		main_menu.hide()
		human_ai_select.hide()
		if !player_select_one.is_AI:
			$"Game UI/RightSideStates/Human Control".visible = true

	else:
		## Check to see if either side has a problem and print both
		if !player1_ready:
			if player_select_one.is_AI:
				printerr("Player 1 doesn't have AI file selected!")
			else:
				printerr("Player 1 doesn't have team name selected!")
			
			if player_select_two.is_AI:
				printerr("Player 2 doesn't have AI file selected!")
			else:
				printerr("Player 2 doesn't have team name selected!")
	
	


func _on_build_pressed() -> void:
	build.emit(true, $"Game UI/RightSideStates/Human Control/Label/SpinBox".value, $"Game UI/RightSideStates/Human Control/Label/SpinBox2".value)



func _update_turns_progressed(new_value):
	$"Game UI/Panel/Turns Progressed".text = "Turns Progressed\n" + str(int(new_value))
