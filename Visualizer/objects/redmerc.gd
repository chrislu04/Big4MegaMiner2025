class_name RedMerc
extends AnimatedSprite2D

@export var box : Panel
var str_name
@export var mouse_detect : Area2D

func _ready() -> void:
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
	
	frame_changed.connect(_on_frame_changed)
	
	if mouse_detect != null:
		mouse_detect.mouse_entered.connect(show_panel)
		mouse_detect.mouse_exited.connect(show_panel)
	
func show_panel():
	box.show()

func hide_panel():
	box.hide()

func _update_values(nam : String, health : int):
	$Panel/VBoxContainer/Name.text = nam
	$Panel/VBoxContainer/HP.text = str(health) + "/20"

func move(direction : Vector2):
	
	match direction.normalized():
		Vector2(-1,0):
			flip_h = false
		Vector2(1,0):
			flip_h = true
	
	play("walk")

func attack(_direction : Vector2):
	
	play("attack")

func idle():
	play("default")

func _on_frame_changed() -> void:
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
