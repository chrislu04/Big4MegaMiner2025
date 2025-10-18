class_name GameUI
extends CanvasLayer



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


func _on_build_pressed() -> void:
	build.emit(true, $"Game UI/RightSideStates/Human Control/Label/SpinBox".value, $"Game UI/RightSideStates/Human Control/Label/SpinBox2".value)

func _update_turns_progressed(new_value):
	$"Game UI/Panel/Turns Progressed".text = "Turns Left\n" + str(int(new_value))


func _on_main_menu_play_game() -> void:
	human_ai_select.visible = true
	main_menu.visible = false


func _on_human_ai_select_go(ready: Variant, ready2: Variant) -> void:
	start_game.emit(ready, ready2)
	main_menu.hide()
	human_ai_select.hide()
	game_ui.show()
	if !ready:
		$"Game UI/RightSideStates/Human Control".visible = true


func _on_human_ai_select_back() -> void:
	main_menu.visible = true
	human_ai_select.visible = false
