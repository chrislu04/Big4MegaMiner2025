extends Control


const CANNON = preload("uid://px2v73fj7qag")


var current_build : Sprite2D
var current_build_name : String
var current_mercenary_dir : String

@export var build_button : Button
@export var destroy_button : Button

@export var merc_up : Button
@export var merc_down : Button
@export var merc_left : Button
@export var merc_right : Button

@export var house : Button
@export var cannon : Button
@export var minigun : Button
@export var cross : Button

@export var house_options : VBoxContainer

var active : bool = false

var build_pos : Vector2 = Vector2.ZERO

signal action(player1 : bool, build : String, x : int, y : int, tower_to_build : String, merc_direction : String)

func _ready() -> void:
	build_button.pressed.connect(_on_build_pressed)
	destroy_button.pressed.connect(_on_destroy_pressed)
	current_build = Sprite2D.new()
	

func _process(_delta: float) -> void:
	
	if GlobalPaths.tile_grid and active:
		current_build.positon = GlobalPaths.tile_grid.get_local_mouse_position()
		
	if Input.is_action_just_pressed("click"):
		action.emit()

func action_made():
	action.emit("build", build_pos.x, build_pos.y, current_build_name ,current_mercenary_dir)

func _on_build_pressed():
	house_options.show()
	GlobalPaths.tile_grid.add_child(current_build)

func _on_destroy_pressed():
	house_options.hide()
	current_build.hide()

func _on_house_pressed():
	pass

func _on_cannon_pressed():
	current_build.texture = CANNON
	current_build_name = "cannon"

func _on_cross_pressed():
	pass

func _on_mini_pressed():
	pass
