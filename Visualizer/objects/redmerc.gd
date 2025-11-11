class_name RedMerc
extends Node2D

var str_name
@export var panel : Panel
@export var mouse_detect : Area2D
@export var sprite_anim: AnimatedSprite2D

func _ready() -> void:
	
	if mouse_detect != null:
		mouse_detect.mouse_entered.connect(show_panel)
		mouse_detect.mouse_exited.connect(show_panel)
	
func show_panel():
	panel.show()

func hide_panel():
	panel.hide()

func _update_values(nam : String, health : int):
	$Panel/VBoxContainer/Name.text = nam
	$Panel/VBoxContainer/HP.text = str(health) + "/20"

func move(direction : Vector2):
	match direction.normalized():
		Vector2(-1,0):
			sprite_anim.flip_h = false
		Vector2(1,0):
			sprite_anim.flip_h = true
	
	sprite_anim.play("walk")

func attack(_direction : Vector2):
	sprite_anim.play("attack")

func idle():
	sprite_anim.play("default")
