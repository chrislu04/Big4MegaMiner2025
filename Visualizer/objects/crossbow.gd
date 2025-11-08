class_name Crossbow
extends Sprite2D

var str_name : String

var targets : Array

@onready var animation_player: AnimationPlayer = $AnimationPlayer

func shoot(target_array):
	for target in targets:
		animation_player.queue("shoot")
		


func _on_animation_player_animation_changed(old_name: StringName, new_name: StringName) -> void:
	if new_name == "shoot":
		targets.pop_front()
		rotation = position.angle_to(targets.front())
