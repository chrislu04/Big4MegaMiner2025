extends Control


const CANNON : Texture = preload("uid://px2v73fj7qag")
const HOUSE = preload("uid://bciq54f3p3yiw")
const CROSSBOW_FIRE = preload("uid://b4dqo57cak8b5")
const GATLING = preload("uid://2cfukvxbe1ah")

const GHOST = preload("uid://26apgdhkxkk7")

var current_build : Sprite2D
var current_build_name : String
var current_mercenary_dir : String

@export var is_player_1 : bool

@export var build_button : Button
@export var destroy_button : Button
@export var queue_button : Button
@export var skip_turn : Button

@export var merc_up : Button
@export var merc_down : Button
@export var merc_left : Button
@export var merc_right : Button

@export var house : Button
@export var cannon : Button
@export var minigun : Button
@export var cross : Button

@export var house_options : HBoxContainer
@export var mercenary_options : HBoxContainer

var active : bool = false

var build_pos : Vector2 = Vector2.ZERO

var current_action : String = ""
var action_active : bool = false

signal action(player1 : bool, build : String, x : int, y : int, tower_to_build : String, merc_direction : String)

func _ready() -> void:
	build_button.pressed.connect(_on_build_pressed)
	destroy_button.pressed.connect(_on_destroy_pressed)
	queue_button.pressed.connect(_on_queue_pressed)
	skip_turn.pressed.connect(skip)
	
	cannon.pressed.connect(_on_cannon_pressed)
	house.pressed.connect(_on_house_pressed)
	minigun.pressed.connect(_on_mini_pressed)
	cross.pressed.connect(_on_cross_pressed)
	
	merc_down.pressed.connect(south)
	merc_up.pressed.connect(north)
	merc_left.pressed.connect(west)
	merc_right.pressed.connect(east)
	
	house_options.hide()
	mercenary_options.hide()
	
	current_build = Sprite2D.new()
	var my_shader = ShaderMaterial.new()
	my_shader.shader = GHOST
	current_build.material = my_shader

func _process(_delta: float) -> void:
	
	if GlobalPaths.tile_grid and active:
		current_build.position = GlobalPaths.tile_grid.get_local_mouse_position().snapped(Vector2(32.0,32.0))
		
	if Input.is_action_just_pressed("click") and current_action != "":
		active = false
		
		action.emit(is_player_1, current_action, current_build.position.x / 32 , current_build.position.y / 32, current_build_name, "")
		current_mercenary_dir = ""
		current_build_name = ""
		
		current_action = ""
		house_options.hide()
		mercenary_options.hide()

func _on_next_turn():
	active = true
	current_build.texture = null
	current_build.hide()

func skip():
	if active:
		action.emit(is_player_1, "Nothing", 0, 0, "", current_mercenary_dir)
		mercenary_options.hide()
		house_options.hide()
		current_action = ""
		current_mercenary_dir = ""

func _on_build_pressed():
	if active:
		house_options.show()
		mercenary_options.hide()
		if current_build.get_parent() == null:
			GlobalPaths.tile_grid.add_child(current_build)
		current_action = "build"

func _on_destroy_pressed():
	if active:
		mercenary_options.hide()
		house_options.hide()
		current_build.hide()
		current_action = "destroy"

func _on_queue_pressed():
	if active:
		house_options.hide()
		mercenary_options.show()
		current_action = ""
	
func _on_house_pressed():
	current_build.show()
	current_build.texture = HOUSE
	current_build.scale = Vector2(32 / CANNON.get_size().x, 32 / CANNON.get_size().y)
	current_build_name = "house"
	

func _on_cannon_pressed():
	current_build.show()
	current_build.texture = CANNON
	current_build.scale = Vector2(32 / CANNON.get_size().x, 32 / CANNON.get_size().y)
	current_build_name = "cannon"
	

func _on_cross_pressed():
	current_build.show()
	current_build.texture = CROSSBOW_FIRE
	current_build.scale = Vector2(32 / CANNON.get_size().x, 32 / CANNON.get_size().y)
	current_build_name = "crossbow"
	current_action = "build"

func _on_mini_pressed():
	current_build.show()
	current_build.texture = GATLING
	current_build.scale = Vector2(32 / CANNON.get_size().x, 32 / CANNON.get_size().y)
	current_build_name = "minigun"
	current_action = "build"

func north():
	current_mercenary_dir = "N"

func south():
	current_mercenary_dir = "S"

func west():
	current_mercenary_dir = "W"

func east():
	current_mercenary_dir = "E"
